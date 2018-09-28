from flask import Flask, render_template, request
from werkzeug.utils import secure_filename
import raw_contract_parser, rule_based
import os,json
app = Flask(__name__)

@app.route('/available_clause/',methods=['GET'])
def available_clause():
    with open('available_clause.json','r') as f:
        return f.read()
	
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

        present_idx = []
        for items in [res.split(',') for res in set(analysis_result)]:
            for i in items:
                tobe_added = int(i)
                if not tobe_added in present_idx:
                    present_idx.append(int(tobe_added))
        present_idx.sort()
        missing_idx = list(set(range(1,10))-set(present_idx))
        missing_idx.sort()
        print(missing_idx)
        missing_clause = []
        present_clause = []
        with open('available_clause.json','r') as f:
            available_clause = json.load(f)
            for idx in present_idx:
                present_clause.append(available_clause['data']['available_clauses'][idx-1]['name']) # results from rule_based start counting at 1
            for idx in missing_idx:
                missing_clause.append(available_clause['data']['available_clauses'][idx-1]['name']) # results from rule_based start counting at 1
        resp = {'data':
                    [{'present_clauses':present_clause},
                    {'missing_clauses':missing_clause}]
                }
        os.remove(fpath)
        return json.dumps(resp)
		
if __name__ == '__main__':
   app.run(debug = True)