from flask import Flask, render_template, request
import json
import time
from requests import get, post
import pandas as pd
from IPython.display import display
app = Flask(__name__)


# Endpoint URL
endpoint = r"https://rnd.cognitiveservices.azure.com/"
apim_key = "6a920a79fbc2465fa1bc9bd94ef59e7e"
post_url = endpoint + "/formrecognizer/v2.1/layout/analyze"
source = r"/Users/User/Downloads/CMS-460-508 Tan enabled (1) (1).pdf"

headers = {
# Request headers
    'Content-Type': 'application/pdf',
    'Ocp-Apim-Subscription-Key': apim_key,
}

params = {
    "includeTextDetails": True,
    "locale": "en-US"
}


@app.route('/upload_pdf', methods = ['POST'])
def extract_pdf():
    print(request.files)
    data_bytes = request.files['pdf'].read()
    errors = {}
    # with open(source, "rb") as f:
    #     data_bytes = f.read()

    try:
        resp = post(url = post_url, data = data_bytes, headers = headers, params = params)
        if resp.status_code != 202:
            print("POST analyze failed:\n%s" % resp.text)
            quit()
        print("POST analyze succeeded:\n%s" % resp.headers)
        get_url = resp.headers["operation-location"]
    except Exception as e:
        print("POST analyze failed:\n%s" % str(e))
        quit()

    
    resp_json = None
    df_dataframe = {}
    multiple_table_entries = {}
    final_df = []
    n_tries = 10
    n_try = 0
    wait_sec = 6
    while n_try < n_tries:
        try:
            resp = get(url = get_url, headers = {"Ocp-Apim-Subscription-Key": apim_key})
            resp_json = json.loads(resp.text)
            if resp.status_code != 200:
                print("GET Receipt results failed:")
                quit()
            status = resp_json["status"]
            if status == "succeeded":
                print("Receipt Analysis succeeded:")
                break
            if status == "failed":
                print("Analysis failed:")
                quit()
            # Analysis still running. Wait and retry.
            time.sleep(wait_sec)
            n_try += 1
        except Exception as e:
            msg = "GET analyze results failed:\n%s" % str(e)
            print(msg)
            quit()
    
    if resp_json is not None:
        pd.options.display.max_columns = None
        Exctracted_text=[]
        for read_result in resp_json["analyzeResult"]["readResults"]:
            print("Page No:%s" % read_result["page"])
            print("---------Page %d: extracted OCR------" % read_result["page"])
            for line in read_result["lines"]:
                print(line["text"])
                Exctracted_text.append(line["text"])

        for pageresult in resp_json["analyzeResult"]["pageResults"]:
            # print("Page No:%s" % pageresult["page"])

            for table in pageresult["tables"]:
                print("--------Page %d Extracted table--------" % pageresult["page"])
                print("Extracted table")
                print("No. of rows %s" % table["rows"])
                print("No. of Columns %s" % table["columns"])
                tableList = [[None for x in range(table["columns"])] for y in range(table["rows"])]
                for cell in table["cells"]:
                    tableList[cell["rowIndex"]][cell["columnIndex"]] = cell["text"]
                # print("new table", tableList)
                df = pd.DataFrame.from_records(tableList)
                df_dataframe = df.to_dict(orient='records')
                df_columns = df.to_dict()
                columns = []
                for key in df_columns:
                    columns.append(key)
                final_df.append({'rows':df_dataframe,'columns':columns})
                #print(df)
        
        
        multiple_table_entries['text'] = Exctracted_text
        multiple_table_entries['multiple_tables'] = final_df

    
    return render_template('output.html', errors=errors, results=multiple_table_entries)

@app.route("/home")
def fileFrontPage():
    return render_template('fileform.html')

if __name__ == '__main__':
    app.run()