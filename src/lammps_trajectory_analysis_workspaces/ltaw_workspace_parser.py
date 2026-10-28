#! /usr/bin/env python3

""" This module creates the parser for the command line arguments

This module's responsibility is to create the top level parser and the subparsers
for this project. Each analysis tool has a corresponding subparser and a  
corresponding subcommand.

We use a factory or builder pattern where each subparser/subcommand has a 
concrete builder that adds the appropriates options, help messages, etc. 

"""
