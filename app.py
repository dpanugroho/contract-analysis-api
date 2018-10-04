from flask import Flask, render_template, request
from werkzeug.utils import secure_filename
import raw_contract_parser, rule_based
import os,json
app = Flask(__name__)

@app.route('/available_clause/',methods=['GET'])
def available_clause():
    with open('available_clause.json','r') as f:
        return f.read()

@app.route('/clause', methods = ['POST'])
def clause():
    phrase = request.form['phrase']
    rule_based_analyzer = rule_based.RuleBased()
    analysis_result = ''.join(rule_based_analyzer.infer([phrase])).split(",")

    resp = {'data':
            {'result':analysis_result}
        }
    return json.dumps(resp)

@app.route('/analyze', methods = ['GET', 'POST'])
def analyze():
   if request.method == 'POST':
        f = request.files['file']
        fpath  = 'temp/'+secure_filename(f.filename)
        f.save(fpath)
    
        parser = raw_contract_parser.RawContractParser()
        clauses = parser.parse_raw_contract(fpath)

        rule_based_analyzer = rule_based.RuleBased()
        analysis_result = rule_based_analyzer.infer(clauses)
        with open('available_clause.json','r') as f:
            available_clause = json.load(f)
            
            # Adding list of present clauses
            details = []
            for clause_idx in range(len(clauses)):
                curr_result = analysis_result[clause_idx]
                # Unrelated clause (analysis result = 0) will not included
                if not "0" in analysis_result[clause_idx]:
                    categories = []
                    for cat_str in curr_result.split(","):
                        categories.append(available_clause['data']['available_clauses'][int(cat_str)-1]['name'])
                    curr_detail = {"clause":clauses[clause_idx],
                                    "categories":categories}
                    details.append(curr_detail)
            present_idx = []
            for items in [res.split(',') for res in set(analysis_result)]:
                for i in items:
                    tobe_added = int(i)
                    if not tobe_added in present_idx:
                        present_idx.append(int(tobe_added))
            present_idx.sort()
            missing_idx = list(set(range(1,10))-set(present_idx))
            missing_idx.sort()
            missing_clause = []
            present_clause = []
        
            for idx in present_idx:
                present_clause.append(available_clause['data']['available_clauses'][idx-1]['name']) # results from rule_based start counting at 1
            for idx in missing_idx:
                missing_clause.append(available_clause['data']['available_clauses'][idx-1]['name']) # results from rule_based start counting at 1
        resp = {'data':
                    [{'present_clauses':present_clause},
                    {'missing_clauses':missing_clause},
                    {'present_clauses_detial':details}]
                }
        os.remove(fpath)
        return json.dumps(resp)
		
if __name__ == '__main__':
   app.run(debug = True)