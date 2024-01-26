from typing import Dict, List, Optional

from librespot.audio.decoders import AudioQuality, VorbisOnlyAudioQuality
from librespot.core import Session
from librespot.metadata import TrackId

import os
import pathlib


BASE62_CHARSET = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'


class Spotify:

    def __init__(self, username: str, password: str, scopes: List[str]):
        """
        Initializes a Spotify instance.

        Parameters:
        - username (str): Spotify username.
        - password (str): Spotify password.
        - scopes (List[str]): List of requested scopes.

        Documentation: https://developer.spotify.com/documentation/web-api/concepts/scopes
        """
        if os.path.exists('creds.json'):
            os.remove('creds.json')
        build = Session.Configuration.Builder().set_stored_credential_file('creds.json').build()
        self.session = Session.Builder(build).user_pass(username, password).create()
        self.token = self.session.tokens().get_token(*scopes).access_token

    def download(self, trackid: str, directory: str, premium: Optional[bool] = True) -> None:
        """
        Downloads a Spotify track.

        Parameters:
        - trackid (str): Spotify track ID.
        - directory (str): Directory to save the downloaded track.
        - premium (bool, optional): Flag indicating premium subscription. Default is True.

        Returns:
        - None
        """
        playable_id = TrackId.from_base62(trackid)
        audio_quality_picker = VorbisOnlyAudioQuality(AudioQuality.VERY_HIGH if premium else AudioQuality.HIGH)
        stream = self.session.content_feeder().load(playable_id, audio_quality_picker, False, None)
        with open(f'{pathlib.Path(directory) / trackid}.ogg', 'wb') as f:
            f.write(stream.input_stream.stream().read())

    def headers(self) -> Dict[str, str]:
        """
        Generates headers for making authenticated requests.

        Returns:
        - Dict[str, str]: Dictionary containing headers.
        """
        return {
            'Authorization': f'Bearer {self.token}',
            'Accept-Language': 'en',
            'Accept': 'application/json',
        }

    @staticmethod
    def gid_to_tid(gid: str) -> str:
        """
        Converts a Spotify GID (Global ID) to a track ID.

        Parameters:
        - gid (str): Spotify GID.

        Returns:
        - str: Spotify track ID.
        """
        gid_decimal, trackid = int(gid, 16), ''
        while gid_decimal > 0:
            remainder = gid_decimal % 62
            trackid = BASE62_CHARSET[remainder] + trackid
            gid_decimal //= 62
        return trackid.swapcase()

    @staticmethod
    def tid_to_gid(trackid: str) -> str:
        """
        Converts a Spotify track ID to a GID (Global ID).

        Parameters:
        - trackid (str): Spotify track ID.

        Returns:
        - str: Spotify GID.

        Test: https://spclient.wg.spotify.com/metadata/4/track/{gid}
        """
        trackid, gid_decimal, base = trackid.swapcase(), 0, 1
        for char in trackid[::-1]:
            digit = BASE62_CHARSET.index(char)
            gid_decimal += digit * base
            base *= 62
        return hex(gid_decimal)[2:].zfill(32)
