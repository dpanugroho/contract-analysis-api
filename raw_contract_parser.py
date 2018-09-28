#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Aug 13 08:48:15 2018

@author: dpanugroho
"""


import textract
import os
import pandas as pd
import spacy
import re
class RawContractParser():
    """Read contract files in docx and load it to excel.

        Note:
            Textract and Pandas library are used in this script.
        
        Example of Usage:
            parser = RawContractParser()                
            parser.create_dataset('Dataset/Contracts/2nd Batch/',\
                                                        'Dataset/Parsed/')
    """
    
    def __init__(self):
        pass
    
    def parse_raw_contract(self, path):
        """Parse single docx file to list of text.

        This function will read a docx file and extract text contained in it. 
        Text will be decoded usng UTF-8 encoding. Text will be transformed to 
        list by spliting at "." character. Extra whitespace will be removed.

        Args:
            path (str): path to the .docx file.
        Return:
            parsed_text (list): list of string of the parsed text.
        """

        if ('.doc' in path or '.pdf' in path):
            parsed_text = textract.process(path)

            parsed_text = parsed_text.decode('utf-8')
            
            doc = spacy.load('en')(parsed_text)
            parsed_text = [re.sub("\s+"," ",s) for s in [sent.string.strip() \
                        for sent in doc.sents] if len(s)>9]
            return parsed_text
        else:
            return "Error when parsing"
    
    