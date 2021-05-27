# taken from https://stackoverflow.com/a/29215357
# SPDX-FileCopyrightText: Holger Just
# SPDX-License-Identifier: CC BY-SA 3.0


import re


# original link on SO is broken:
#   http://blogs.msdn.com/b/twistylittlepassagesallalike/archive/2011/04/23/
#   everyone-quotes-arguments-the-wrong-way.aspx
# same link on web-archive:
#   https://web.archive.org/web/20161228144344/https://blogs.msdn.microsoft.com/
#   twistylittlepassagesallalike/2011/04/23/
#   everyone-quotes-command-line-arguments-the-wrong-way/


def cmd_escape_arg(arg):
    # Escape the argument for the cmd.exe shell.
    #
    # First we escape the quote chars to produce a argument suitable for
    # CommandLineToArgvW. We don't need to do this for simple arguments.

    if not arg or re.search(r'(["\s])', arg):
        arg = '"' + arg.replace('"', r'\"') + '"'

    return _inner_escape(arg)


def _inner_escape(arg):
    # Escape an argument string to be suitable to be passed to
    # cmd.exe on Windows
    #
    # This method takes an argument that is expected to already be properly
    # escaped for the receiving program to be properly parsed. This argument
    # will be further escaped to pass the interpolation performed by cmd.exe
    # unchanged.
    #
    # Any meta-characters will be escaped, removing the ability to e.g. use
    # redirects or variables.
    #
    # @param arg [String] a single command line argument to escape for cmd.exe
    # @return [String] an escaped string suitable to be passed as a program
    #   argument to cmd.exe

    meta_chars = '()%!^"<>&|'
    meta_re = re.compile(
        '(' + '|'.join(re.escape(char) for char in list(meta_chars)) + ')')
    meta_map = {char: "^%s" % char for char in meta_chars}

    def escape_meta_chars(m):
        char = m.group(1)
        return meta_map[char]

    return meta_re.sub(escape_meta_chars, arg)
