import argparse
import collections
import logging
import re

from .. import api
from ..command import CMD_SUCCESS, HELP_LIST
from .autoprofile import AutoProfile
from ..exceptions import NotFoundError, InvalidValueError


AUTOBOT_COMMAND_USAGE_MSG = """%(prog)s autoprofile <source> ... <source>"""
USERNAME_BOT_REGEX = r"\bbot\b"

logger = logging.getLogger(__name__)


class AutoBot(AutoProfile):
    """Auto-detect users that look like bots.
    This command dumbly assumes that anyone with the word "bot" in their username is a bot.
    """
    @property
    def description(self):
        return """Auto-detects bot identities."""

    @property
    def usage(self):
        return AUTOBOT_COMMAND_USAGE_MSG

    def run(self, *args):
        """Autodetect bot identities."""

        params = self.parser.parse_args(args)
        sources = params.source
        code = self.mark_bots(sources)

        return code

    def mark_bots(self, sources):
        """Detect bots among the identities in the given sources, and mark them.
        """

        identities = self.__select_autocomplete_identities(sources)
        bot_pattern = re.compile(USERNAME_BOT_REGEX, re.IGNORECASE)

        for uuid, ids in identities.items():
            # Among the identities (with the same priority) selected
            # to complete the profile, it will choose the longest 'name'.
            # If no name is available, it will use the field 'username'.
            is_bot = False

            for identity in ids:
                username = identity.username
                if self.probably_a_bot(identity.username, bot_pattern):
                    is_bot = True

            kw = {
                'is_bot': is_bot,
            }

            try:
                api.edit_profile(self.db, uuid, **kw)
                self.display('autoprofile.tmpl', identity=identity)
            except (NotFoundError, InvalidValueError) as e:
                self.error(str(e))
                return e.code

            return CMD_SUCCESS

    def probably_a_bot(self, username, bot_pattern):
        """Returns True if the given username probably belongs to a bot."""
        
        return bot_pattern.search(username)
