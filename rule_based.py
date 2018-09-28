#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Created on Mon Aug  6 09:37:55 2018

@author: dpanugroho

Rule-based approach for part of contract classification/extraction
"""

import re
import spacy

class RuleBased:
    def __init__(self, checkers = []):
        self.nlp=spacy.load('en')    
        ALL_VALID_CHECKERS = ['regex','word_dependence','list']
        if checkers == []:
            self.checkers = ALL_VALID_CHECKERS
        else:
            try:
                assert not isinstance(checkers, str)
                for checker in checkers:
                    if not checker in ALL_VALID_CHECKERS:
                        raise ValueError("{} is invalid, available checkers are [{}]"
                              .format(checker, ','.join(ALL_VALID_CHECKERS)))
                    else:
                        self.checkers = checkers
            except (TypeError, AssertionError):
                raise TypeError("checker parameter must be list of valid checkers: \
                      [{}]".format(','.join(ALL_VALID_CHECKERS)))
                
    def check_in_children(self, token, qChild):
        res = False
        if qChild in [child.lemma_ for child in token.children]:
            res = True
        else:
            for child in token.children:
                res = res or self.check_in_children(child, qChild)
        return res
    
    def traverse_dependency_tree(self, doc,qHead,qChild):
        if not qHead in [token.lemma_ for token in doc]:
            return False
        else:
            token = [t for t in doc if t.lemma_==qHead][0]
            return self.check_in_children(token,qChild)

    def check_regex(self, text, res):
        """Function to identify label by word occurence using regular
        expression
    
        Args:
            text (list): clause text.
            res (str): current result set/predicted label for this clause.
    
        Returns:
            res (str): modified result set. 
    
        """
        res = []
        limitation_of_liability = \
            re.search('((((liability)'
                          '|obligation|liable).*(((?<!not )(be )?(limited))'
                          '|(exceed)))|(exclusive remedy)|(exclusive remedies)'
                          '|(limitation.* of liability)|(no further liability)'
                          '|(only liability)|(((limit)'
                          '|(exclude)).+(liability)))'
                      , text)
        general_liability_exclusions_or_disclaimer = \
            re.search('((((shall)|(will)) not be )(held )?((liable)'
                         '|(responsible))|(no ((liability)|(responsibility)))'
                         '|((not ((accept)|(responsible))).*(claim))'
                         '|((claim).*(exclude))|((either).*(liable))'
                         '|((excluded).*(liability))|(((liable)|(claim)'
                         '|(exclude)).*((loss)|(lost)))|((no event).*((liable)'
                         '|(liability))))'
                      , text)
        liability_to_pay_damages_cost_expense_in_specified_events = \
            re.search('((indemni)|(liquidated damage)|((claim).+((los)'
                       '|(damage)|(injury)))|(reimburse)|(compensat))'
                      , text)
        intellectual_property_assignment = \
            re.search('((intellectual property)|((property).+(right))'
                        '|((remain).+(property)))'
                      , text)
        warranties = re.search('((warrant)|((free).*(defect)))', text)
        termination_or_cancellation = \
            re.search('((?<!survive the )(terminat)|(cancel)|(suspend)|(cease)'
                        '|(change of control)|(insolven))'
                      , text)
        consequences_of_termination_or_cancellation = \
            re.search('((((cancel)|(terminat)).{20,}((shall)|(liable)|(will)'
                          '|(charge)|(cost)|(damage)|(loss))))'
                      , text)
        timing_of_delivery = \
            re.search('((delay)|((deliver).*(((?<!any )(time))|(date)'
                        '|(schedule)))|((((?<!any )(time))|(date)'
                        '|(schedule)).*(deliver))|((delivery).*((estimat)|(approximate))))'
                      , text)
        force_majeure = \
            re.search('((force majeure)|(((beyond)|(outside)).*(control))'
                        '|(catastrophe)|(disaster))'
                      , text)
        governing_law = \
            re.search('((under the law)|(jurisdiction of)'
                        '|(according to the law)|(governing law))'
                      , text)
        
        if limitation_of_liability:
            res.append(1)
        if general_liability_exclusions_or_disclaimer:
            res.append(2)
        if liability_to_pay_damages_cost_expense_in_specified_events:
            res.append(3)
        if intellectual_property_assignment:
            if (not re.search('(good)', text) or re.search('(intellectual property)', text)):
                res.append(4)
            if re.search('(infringe)', text):
                res = list(filter(lambda c: c!=4, res))
        if warranties:    
            if not re.search('((,..{0,10},.{0,10}(warrant))'
                               '|(,.{0,10}(warrant).{0,10},))'
                             , text):  
                res.append(5)

        if termination_or_cancellation:
            res.append(6)
        if consequences_of_termination_or_cancellation \
            and not timing_of_delivery or termination_or_cancellation \
            and liability_to_pay_damages_cost_expense_in_specified_events:
            if not re.search('((shall terminate)|(shall cancel))', text):
                res.append(7)
        if timing_of_delivery:
            res.append(8)
        if force_majeure:
            res.append(9)
        if governing_law:
            res.append(10)

        return res
    def check_word_dependency(self, text, res):
        """Function to identify label using gramatical dependency
    
        Args:
            text (list): clause text.
            res (str): current result set/predicted label for this clause.
    
        Returns:
            res (str): modified result set. 
    
        """
    
        # "not exceed" is the synonim for "be limited"
        text = text.replace('not exceed','be limited') 
        text = text.replace('assumes','assume') 
        text = text.replace('responsibility','liability') 

        
        # If the text says that the "liability" is "limited", then it is
        # considered as limitation of liabilities
        doc = self.nlp(text)
        for chunk in doc.noun_chunks:
            if (chunk.root.text == 'liability' and chunk.root.head.text=='limited'):
                res.append(1)
        if self.traverse_dependency_tree(doc, 'liability', 'limited'):
            res.append(1)
        if self.traverse_dependency_tree(doc, 'limited', 'liability'):
            res.append(1)
        if self.traverse_dependency_tree(doc, 'liability', 'exceed'):
            res.append(1)
        if self.traverse_dependency_tree(doc, 'exceed', 'liability'):
            res.append(1)
        for token in doc:
            children = set([child.lemma_ for child in token.children])
            if (token.dep_ == 'ROOT' and (
                    {'not','liability'}.issubset(children)
                    or {'not','liable'}.issubset(children)
                    or {'not','claim'}.issubset(children)
                    or {'not','responsible'}.issubset(children)
                    or {'defend','claim'}.issubset(children))):
                    res.append(2)
            if (token.dep_ == 'det' and token.text == 'no' 
                and token.head.text in ['liability','responsibility']):
                    res.append(2)
            if ((token.text == 'reimburse') and (token.dep_ == 'ROOT')):
                    res.append(3)
            if (token.dep_ == 'ROOT' and (
                     {'reimburse'}.issubset(children)
                    or {'compensate'}.issubset(children)
                    or {'recover'}.issubset(children))):      
                    res.append(3)
            if ((token.dep_ == 'ROOT' 
                 and token.lemma_ in ['warrant','guarantee'])):
                res.append(5)
                res = list(filter(lambda c: c!=4, res))
            if (token.text in ['is','are'] and (set(["date", "estimate"])\
                .issubset(set(children)) or set(["date","approximate"])\
                .issubset(set(children)))):
                res.append(8)
#            if ((token.dep_ == 'ROOT' 
#                 and token.text == 'governed')):
#                res.append(10)
        
        # Checking time-essence relationship
        if set([('time','nsubj'),('essence','pobj')]).issubset([(token.lemma_, token.dep_) for token in doc]):
            res.append(8)
        # Checking delay in delivery relationship
        if self.traverse_dependency_tree(doc, 'delay','delivery'):
            res.append(8)

        if ((self.traverse_dependency_tree(doc,'deliver','good') or \
             self.traverse_dependency_tree(doc,'deliver','product')) and \
                (self.traverse_dependency_tree(doc, 'deliver','time') or \
                 self.traverse_dependency_tree(doc, 'deliver','date') or \
                 self.traverse_dependency_tree(doc, 'delay','deliver') or \
                 self.traverse_dependency_tree(doc,'deliver','timely') or \
                 self.traverse_dependency_tree(doc, 'deliver','delay'))):
                res.append(8)
        if ((self.traverse_dependency_tree(doc,'delivery','good') or \
             self.traverse_dependency_tree(doc,'delivery','product')) and \
                (self.traverse_dependency_tree(doc, 'delivery','time') or \
                 self.traverse_dependency_tree(doc, 'delivery','date') or \
                 self.traverse_dependency_tree(doc, 'delay','delivery') or \
                 self.traverse_dependency_tree(doc,'delivery','timely') or \
                 self.traverse_dependency_tree(doc, 'delivery','delay'))):
                res.append(8)
        if self.traverse_dependency_tree(doc, 'liable', 'delay'):
            res.append(8)
        if self.traverse_dependency_tree(doc, 'liability', 'delay'):
            res.append(8)
        if self.traverse_dependency_tree(doc, 'delay','supply'):
            res.append(8)
        if self.traverse_dependency_tree(doc, 'govern','law'):
            res.append(10)
        return res
    
    def warranty_list_checker(self, documents, res):
        """Function to detect listing of warranties
    
        This function will detect phrase like "The seller warrants that.."
        and mark the sentence itself and the following sentences as warranty
        class (identified lower case at beginning of the sentence)
    
        Args:
            document (list): List of clause text.
            res (str): Current result set/predicted label (whole dataset).
    
        Returns:
            None: 
    
        
        The function update value of res
    
        """
        for i in range(len(documents)):
            clause = documents[i]
            if (re.search('(warrant)', clause) 
                and re.search('(that)', clause) 
                and len(clause.split(' '))<10):
                is_next_line_start_lower_sentence = True
                c = i
                while is_next_line_start_lower_sentence:
                    res[c] += ',5'
                    is_next_line_start_lower_sentence = documents[c+1][0].islower()
                    c+=1
    def termination_list_checker(self, documents, res):
        """Function to detect listing of termination conditions
    
        This function will look for root token with "termination" as its text
        and having 'may' as on of token children. After that, it will look at 
        the following lines and marked it as termination class if it starts 
        with numbering or lower case letter (Upper case tend to be detected
        after the context is changed, thus signaling the end of termination 
        context)
    
        Args:
            document (list): List of clause text.
            res (str): Current result set/predicted label (whole dataset).
    
        Returns:
            None: 
    
        
        The function update value of res
    
        """
        for i in range(len(documents)):
            clause = documents[i].lower()
            root_token = [tok for tok in self.nlp(clause) if tok.dep_ == 'ROOT'][0]
            if (((root_token.lemma_ == 'terminate') 
                        and (('may' in [child.text for child in root_token.children]) 
                            or ('be' in [child.text for child in root_token.children])))
                    or (set(['terminate','may']).issubset(set([child.text for child in root_token.children])))
                    or re.search('cancel', clause)):
                is_next_line_start_lower_sentence = True
                c = i
                while is_next_line_start_lower_sentence:
                    res[c] += ',6'
                    is_next_line_start_lower_sentence = documents[c+1][0].islower()
                    c+=1
    def timing_not_on_time_consequence_checker(self, documents, res):
        """Function to detect listing of consequence of timing delivery. 
    
        This function will look for consequence if delivery not be made on 
        time. The function will loook for sentence where "deliver" is the 
        lemma and both "not" and "on" are found in the token children.
        After that, it will look at the following lines and marked it as 
        timing of delivery class if it starts with numbering or lower case letter 
        (Upper case tend to be detected after the context is changed, thus 
        signaling the end of delivery time context)
    
        Args:
            document (list): List of clause text.
            res (str): Current result set/predicted label (whole dataset).
    
        Returns:
            None: 
    
        
        The function update value of res
    
        """
        for i in range(len(documents)):
            clause = documents[i].lower()
            deliver_token = [tok for tok in self.nlp(clause)\
                             if tok.lemma_ == 'deliver']
            if len(deliver_token)>0:
                deliver_token = deliver_token[0]
                if set(['not','on']).issubset(set([c.text for c \
                    in deliver_token.children])):
                    is_next_line_start_lower_sentence = True
                    c = i
                    while is_next_line_start_lower_sentence:
                        res[c] += ',8'
                        is_next_line_start_lower_sentence = documents[c+1][0].islower()
                        c+=1
        
            if self.traverse_dependency_tree(self.nlp(clause),'delay','delivery'):
                    is_next_line_start_lower_sentence = True
                    c = i
                    while is_next_line_start_lower_sentence:
                        res[c] += ',8'
                        is_next_line_start_lower_sentence = documents[c+1][0].islower()
                        c+=1
                                    
    def infer(self, documents): 
        """Function infer list of clauses
    
        Args:
            documents (list): list of clauses.
    
        Returns:
            result (str): predicted label from documents.
    
        """
        results = []
        for doc in documents:
            curr_doc_res = []
            
            if 'regex' in self.checkers:
                curr_doc_res = (self.check_regex(doc.lower(), curr_doc_res))
            if 'word_dependence' in self.checkers:
                curr_doc_res = (self.check_word_dependency(doc.lower(),curr_doc_res))
            curr_doc_res = list(set(curr_doc_res))
            
            
            if curr_doc_res:
                curr_doc_res = ','.join(str(x) for x in curr_doc_res)
            else:
                curr_doc_res = '0'
            results.append(curr_doc_res)
        
        if 'list' in self.checkers:
            self.warranty_list_checker(documents, results)
            self.termination_list_checker(documents, results)
            self.timing_not_on_time_consequence_checker(documents, results)

        return (results)
        

			