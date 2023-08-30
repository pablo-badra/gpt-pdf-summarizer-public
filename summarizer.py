import os
from flask import Flask, request
from werkzeug.utils import secure_filename
import openai
from PyPDF2 import PdfReader
import threading
from IPython.display import display, HTML
from flask import Flask, request, redirect, url_for

class DocumentSummarizer:
    def __init__(self, api_key, model="gpt-3.5-turbo", temperature=0.1, max_tokens=1054, top_p=0.5, frequency_penalty=0.7, presence_penalty=0.7, max_dim=1024, max_sentences=range(5)):
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.top_p = top_p
        self.frequency_penalty = frequency_penalty
        self.presence_penalty = presence_penalty
        self.max_dim = max_dim
        self.max_sentences = max_sentences
        openai.api_key = self.api_key

    def get_completion(self, prompt): 
        messages = [
            {"role": "system", "content": "You are a highly intelligent AI attorney assistant."},
            {"role": "user", "content": prompt}
        ]
        response = openai.ChatCompletion.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature, 
            max_tokens=self.max_tokens,
            top_p=self.top_p,
            frequency_penalty=self.frequency_penalty,
            presence_penalty=self.presence_penalty,
        )
        return response.choices[0].message["content"]

    def get_num_pages_from_pdf(self, filename):
        reader = PdfReader(filename)
        return len(reader.pages)

    def text_from_pdf(self, filename, page_to_extract=-1, max_words=4097):
        reader = PdfReader(filename)
    
        text = ''
        if (page_to_extract == -1):
            for page in reader.pages:
                text_tmp = page.extract_text()
                text_tmp = text_tmp.replace("\n", "")
                text += text_tmp
        else:
            if (page_to_extract > len(reader.pages)):
                return -1
        
            page = reader.pages[page_to_extract]
            text_tmp = page.extract_text()
            text_tmp = text_tmp.replace("\n", "")
            text += text_tmp

        words = text.split(" ")

        if len(words) > max_words:
            words = words[:max_words]

        return ' '.join(words)

    def summarize_pages(self, filename):
        num_pages = self.get_num_pages_from_pdf(filename)
        previous_response = ""
        responses_all = ""
        
        for p in range(0, num_pages):
            text = self.text_from_pdf(filename, page_to_extract=p, max_words=self.max_dim)

            prompt = f"""Summarize the provided legal text fragment. At the end of each summary, answer the following questions in bullet point format: What is the procedural history of the case, including both criminal and immigration-related proceedings.
            Were law enforcement reports admitted during immigration proceedings? These reports could be from police, probation, and parole officers and may include documents like police reports, presentence reports, probation reports, autopsy reports, etc. If these reports were admitted in court, how much weight or importance did the court assign to them? The summaries should provide a comprehensive yet concise overview of each case, focusing particularly on the interaction between criminal and immigration proceedings and the usage of law enforcement reports. Do not repeat information summarized from the previous text fragment: Previous text framgment: ```{previous_response}``` NEW TEXT FRAGMENT TO SUMMARIZE:
                    ```{text}```
                    """
        
            response = self.get_completion(prompt)
            response = 'Page ' + str(p) + '\n' + response
            responses_all += response
            previous_response = response
            print ('Page ' + str(p))

        responses_all = 'All Summary Fragments: ' + responses_all
        return responses_all

    def consolidate_summaries(self, responses_all):
        prompt = f"""I am providing you with a set of AI generated summaries for, one for each page of a legal document. Consolidate all of these summaries into one single summary, with a maximum of 4 paragraphs. Ensure information missing at the start of the summaries is accounted for later on. The summaries should provide a comprehensive yet concise overview of each case, focusing particularly on the interaction between criminal and immigration proceedings and the usage of law enforcement reports. 

        At the end of the summary, answer the following questions in bullet point format: 

        What is the procedural history of the case, including both criminal and immigration-related proceedings.
        Were law enforcement reports  admitted during immigration proceedings? These reports could be from police, probation, and parole officers and may include documents like police reports, pre-sentence reports, probation reports, autopsy reports, etc. 

        If these reports were admitted in court, how much weight or importance did the court assign to them? Use newline characters in your response. TEXT: ```{responses_all}```"""

        final_response = self.get_completion(prompt)
        return final_response



# Your other imports go here
# from summarizer import DocumentSummarizer

# Load OpenAI API key from environment variables
# openai_api_key = os.getenv('OPENAI_API_KEY')
openai_api_key = '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'

# Initialize summarizer
# summarizer = DocumentSummarizer(openai_api_key)

UPLOAD_FOLDER = '/Users/stjames/Documents/projects/summarize'

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() == 'pdf'

upload_style = '''
body {
    background-color: #FDFCFB;  /* updated to slight cream white */
    font-family: 'Times New Roman', Times, serif;
    color: #000000;  /* updated to black */
}
h1, .marquee {
    text-align: center;
    color: #000000;  /* updated to black */
    text-shadow: 2px 2px #999999;
    font-weight: bold;
    font-style: italic;
}
form {
    margin-top: 50px;
    text-align: center;
}
.btn {
    background-color: #cccccc;
    color: #000000;  /* updated to black */
    border-radius: 0;
    padding: 10px;
    font-size: 20px;
    cursor: pointer;
}
.btn:hover {
    background-color: #999999;
    color: #000000;  /* updated to black */
}
.marquee {
    overflow: hidden;
    white-space: nowrap;
    animation: marquee 10s linear infinite;
}
@keyframes marquee {
    0% { text-indent: 100%; }
    100% { text-indent: -100%; }
}
'''

summary_style = '''
body {
    background-color: #FDFCFB;  /* updated to slight cream white */
    font-family: 'Times New Roman', Times, serif;
    color: #000000;  /* updated to black */
}
h1 {
    text-align: center;
    color: #000000;  /* updated to black */
    text-shadow: 2px 2px #999999;
}
.content {
    margin: 50px;
    white-space: pre-wrap; /* to maintain line breaks in text */
    border: 2px solid #000000;  /* updated to black */
    padding: 20px;
}
.loader {
    border: 16px solid #cccccc;
    border-radius: 50%;
    border-top: 16px solid #000000;  /* updated to black */
    width: 120px;
    height: 120px;
    animation: spin 2s linear infinite;
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    display: none; 
}
@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}
'''



@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            return 'No file part'
        file = request.files['file']
        if file.filename == '':
            return 'No selected file'
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            
            # Redirect to the summarization page
            return redirect(url_for('summarize_file', filename=filename))

    html_template = '''
    <!doctype html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>Upload PDF</title>
        <style>
            {}
        </style>
    </head>
    <body>
        <h1>Upload your PDF.</h1>
        <div class="marquee">cheater</div>
        <form method="post" enctype="multipart/form-data">
            <input type="file" name="file"><br><br>
            <button type="submit" class="btn">Upload</button>
        </form>
    </body>
    </html>
    '''

    return html_template.format(upload_style)

@app.route('/summarize/<filename>', methods=['GET'])
def summarize_file(filename):
    if allowed_file(filename):
        filename = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if os.path.exists(filename):
            # Initialize summarizer
            summarizer = DocumentSummarizer(openai_api_key)

            # Use the summarizer to summarize the document and print the final summary
            summaries = summarizer.summarize_pages(filename)
            final_summary = summarizer.consolidate_summaries(summaries)
            
            # Log the completion of the summarization
            app.logger.info("Summarized file: " + filename)
            
            html_template = '''
            <!doctype html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1">
                <title>Summary</title>
                <style>
                    {}
                </style>
                <script>
                    window.onload = function() {{
                        document.getElementById("loader").style.display = "none";
                    }}
                </script>
            </head>
            <body>
                <div id="loader" class="loader"></div>
                <h1>Summary</h1>
                <div class="content">{}</div>
            </body>
            </html>
            '''
            return html_template.format(summary_style, final_summary)
        else:
            return 'File not found. Please upload the file again.'
    else:
        return 'Invalid file type. Please upload a .pdf file'


if __name__ == "__main__":
    app.run(debug=True, port=5025)

