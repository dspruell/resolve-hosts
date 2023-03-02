# resolve-hosts
Resolve list of DNS hostnames.

This is a Python module designed to fit the need of a simple app that can
query an input list of DNS names and output their resolved IP addresses. It
defaults to using the local system resolver for lookups, but can instead
use a list of one or more custom DNS resolvers supplied on the command line.

## Installation
This is a setuptools package; install using pip:

```
pip install resolve-hosts
```

It's recommended to use [pipx](https://pypa.github.io/pipx/) for easy setup and
isolation:

```
pipx install resolve-hosts
```

## Usage
The module installs a command line tool called `resolve-hosts` that should be
in your `PATH`. For a usage overview, see the output of `resolve-hosts -h`. 

Feed it a newline-separated list of names as a parameter. To read from
standard input, omit the parameter or use `-` for the input.

A file with a few sample names to resolve is in the `tests/` folder.

Example using the local system resolver:

```
$ resolve-hosts tests/testnames.txt 
www.example.com             93.184.216.34
blocked.test.on.quad9.net   NXDOMAIN
mxs.mail.ru                 94.100.180.31 217.69.139.150
magnolia.ns.cloudflare.com  172.64.34.214 108.162.194.214 162.159.38.214
```

The above system is clearly configured to use [Quad9](https://www.quad9.net/)
resolvers, as the local resolver returned NXDOMAIN for the test FQDN.

Using specified resolvers and debug output enabled:

```
$ resolve-hosts -s 8.8.4.4 -s 8.8.8.8 -d tests/testnames.txt 
[DEBUG] configured to use resolver(s): ['8.8.4.4', '8.8.8.8']
[DEBUG] effective resolver address(es): ['8.8.4.4', '8.8.8.8']
www.example.com             93.184.216.34
blocked.test.on.quad9.net   127.0.0.1
mxs.mail.ru                 217.69.139.150 94.100.180.31
magnolia.ns.cloudflare.com  172.64.34.214 108.162.194.214 162.159.38.214
```

JSON output from data on stdin:

```
$ resolve-hosts -j < tests/testnames.txt 
{
    "data": [
        {
            "www.example.com": [
                "93.184.216.34"
            ]
        },
        {
            "blocked.test.on.quad9.net": [
                "NXDOMAIN"
            ]
        },
        {
            "mxs.mail.ru": [
                "217.69.139.150",
                "94.100.180.31"
            ]
        },
        {
            "magnolia.ns.cloudflare.com": [
                "162.159.38.214",
                "108.162.194.214",
                "172.64.34.214"
            ]
        }
    ]
}
```

