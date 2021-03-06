#!/usr/bin/env python3.6
# -*- coding: utf-8 -*-

"""
Copyright (C) 2013-2017  Markus Ottela

This file is part of TFC.

TFC is free software: you can redistribute it and/or modify it under the terms
of the GNU General Public License as published by the Free Software Foundation,
either version 3 of the License, or (at your option) any later version.

TFC is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with TFC. If not, see <http://www.gnu.org/licenses/>.
"""

import os
import typing

from typing import Any, Callable, List

from src.common.crypto   import auth_and_decrypt, encrypt_and_sign, hash_chain
from src.common.errors   import CriticalError
from src.common.encoding import str_to_bytes, int_to_bytes
from src.common.encoding import bytes_to_str, bytes_to_int
from src.common.misc     import ensure_dir, split_byte_string
from src.common.statics  import *

if typing.TYPE_CHECKING:
    from src.common.db_masterkey import MasterKey
    from src.common.db_settings  import Settings


class KeySet(object):
    """KeySet object handles frequently changing data (keys and haracs) of contacts."""

    def __init__(self,
                 rx_account: str,
                 tx_key:     bytes,
                 rx_key:     bytes,
                 tx_hek:     bytes,
                 rx_hek:     bytes,
                 tx_harac:   int,
                 rx_harac:   int,
                 store_keys: Callable) -> None:
        """Create a new keyset object.

        :param rx_account: Use account as UID for each recipient
        :param tx_key:     Forward secret message key for sent messages
        :param rx_key:     Forward secret message key for received messages (RxM only)
        :param tx_hek:     Static header key for hash ratchet counter encryption
        :param rx_hek:     Static header key for hash ratchet counter decryption (RxM only)
        :param tx_harac:   Hash ratchet counter for sent messages
        :param rx_harac:   Hash ratchet counter for received messages
        :param store_keys: Reference to KeyLists's method that writes all keys to db.
        """
        self.rx_account = rx_account
        self.tx_key     = tx_key
        self.rx_key     = rx_key
        self.tx_hek     = tx_hek
        self.rx_hek     = rx_hek
        self.tx_harac   = tx_harac
        self.rx_harac   = rx_harac
        self.store_keys = store_keys

    def dump_k(self) -> bytes:
        """Return keyset data as constant length byte string."""
        return str_to_bytes(self.rx_account) \
               + self.tx_key \
               + self.rx_key \
               + self.tx_hek \
               + self.rx_hek \
               + int_to_bytes(self.tx_harac) \
               + int_to_bytes(self.rx_harac)

    def rotate_tx_key(self) -> None:
        """Update TxM side tx-key and harac (provides forward secrecy for messages)."""
        self.tx_key    = hash_chain(self.tx_key)
        self.tx_harac += 1
        self.store_keys()

    def update_key(self, direction: str, key: bytes, offset: int) -> None:
        """Update RxM side tx/rx-key and harac."""
        if direction == 'tx':
            self.tx_key    = key
            self.tx_harac += offset
            self.store_keys()

        if direction == 'rx':
            self.rx_key    = key
            self.rx_harac += offset
            self.store_keys()


class KeyList(object):
    """KeyList object manages list of keyset objects and encrypted keyset database.

    The keyset database is separated from contact database as trickle connection needs to update
    keys frequently with no risk of read/write queue blocking that occurs e.g. when new nick is
    being stored.
    """

    def __init__(self, master_key: 'MasterKey', settings: 'Settings') -> None:
        """Create a new key list object."""
        self.master_key = master_key
        self.settings   = settings
        self.keysets    = []  # type: List[KeySet]
        self.file_name  = f'{DIR_USER_DATA}/{settings.software_operation}_keys'

        if os.path.isfile(self.file_name):
            self.load_keys()
        else:
            self.store_keys()

    def load_keys(self) -> None:
        """Load keys from encrypted database."""
        ensure_dir(f'{DIR_USER_DATA}/')
        with open(self.file_name, 'rb') as f:
            ct_bytes = f.read()

        pt_bytes = auth_and_decrypt(ct_bytes, self.master_key.master_key)
        keysets  = split_byte_string(pt_bytes, item_len=1168)  # 1024 + 4 * 32 + 2 * 8
        dummy_id = 'dummy_contact'.encode('utf-32')
        keysets  = [k for k in keysets if not k.startswith(dummy_id)]

        for k in keysets:
            rx_account = bytes_to_str(k[0:1024])
            tx_key     = k[1024:1056]
            rx_key     = k[1056:1088]
            tx_hek     = k[1088:1120]
            rx_hek     = k[1120:1152]
            tx_harac   = bytes_to_int(k[1152:1160])
            rx_harac   = bytes_to_int(k[1160:1168])

            self.keysets.append(KeySet(rx_account,
                                       tx_key, rx_key,
                                       tx_hek, rx_hek,
                                       tx_harac, rx_harac,
                                       self.store_keys))

    def store_keys(self) -> None:
        """Write keys to encrypted database."""
        num_of_dummies = self.settings.m_number_of_accnts - len(self.keysets)
        dummy_keyset   = self.generate_dummy_keyset()

        pt_bytes  = b''.join([k.dump_k() for k in self.keysets])
        pt_bytes += num_of_dummies * dummy_keyset
        ct_bytes  = encrypt_and_sign(pt_bytes, self.master_key.master_key)

        ensure_dir(f'{DIR_USER_DATA}/')
        with open(self.file_name, 'wb+') as f:
            f.write(ct_bytes)

    @staticmethod
    def generate_dummy_keyset() -> bytes:
        """Generate bytestring for dummy keyset."""
        tx_account = str_to_bytes('dummy_contact')
        tx_key     = bytes(32)
        rx_key     = bytes(32)
        tx_hek     = bytes(32)
        rx_hek     = bytes(32)
        tx_harac   = int_to_bytes(0)
        rx_harac   = int_to_bytes(0)

        return tx_account + tx_key + rx_key + tx_hek + rx_hek + tx_harac + rx_harac

    def get_keyset(self, account: str) -> KeySet:
        """Load keyset from list based on unique account name."""
        return next(k for k in self.keysets if account == k.rx_account)

    def has_local_key(self) -> bool:
        """Return True if local key exists."""
        return any(k.rx_account == 'local' for k in self.keysets)

    def has_keyset(self, account: str) -> bool:
        """Return True if contact with account exists."""
        return any(account == k.rx_account for k in self.keysets)

    def add_keyset(self, rx_account: str, tx_key: bytes, rx_key: bytes, tx_hek: bytes, rx_hek: bytes) -> None:
        """Add new keyset to key list, write changes to database."""
        if self.has_keyset(rx_account):
            self.remove_keyset(rx_account)
        self.keysets.append(KeySet(rx_account, tx_key, rx_key, tx_hek, rx_hek, 0, 0, self.store_keys))
        self.store_keys()

    def remove_keyset(self, name: str) -> None:
        """Remove keyset from keys based on account, write changes to database."""
        for i, k in enumerate(self.keysets):
            if name == k.rx_account:
                del self.keysets[i]
                self.store_keys()
                break

    def change_master_key(self, master_key: 'MasterKey') -> None:
        """Change master key, write changes to database."""
        self.master_key = master_key
        self.store_keys()

    def manage(self, command: str, *params: Any) -> None:
        """Manage keyset database based on data received over km_queue."""
        if command == 'ADD':
            self.add_keyset(*params)
        elif command == 'REM':
            self.remove_keyset(*params)
        elif command == 'KEY':
            self.change_master_key(*params)
        else:
            raise CriticalError("Invalid KeyList management command.")
