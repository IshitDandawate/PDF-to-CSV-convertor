import pypdfium2 as pdfium
import sys
from PIL import Image
from io import BytesIO
from pytesseract import image_to_string
import google.generativeai as genai
from dotenv import load_dotenv
import os
import csv

load_dotenv()

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

# Configure API key for Google Generative AI
genai.configure(api_key=os.getenv("API_KEY"))

model = genai.GenerativeModel('gemini-1.5-flash')

def convert_pdf_to_images(file_path, scale=300/72):
    pdf_file = pdfium.PdfDocument(file_path)  
    page_indices = [i for i in range(len(pdf_file))]
    
    renderer = pdf_file.render(
        pdfium.PdfBitmap.to_pil,
        page_indices=page_indices,
        scale=scale,
    )
    
    list_final_images = [] 
    
    for i, image in zip(page_indices, renderer):
        image_byte_array = BytesIO()
        image.save(image_byte_array, format='jpeg', optimize=True)
        image_byte_array = image_byte_array.getvalue()
        list_final_images.append({i: image_byte_array})
    
    return list_final_images

def extract_text_with_pytesseract(list_dict_final_images):
    image_list = [list(data.values())[0] for data in list_dict_final_images]
    image_content = []
    
    for image_bytes in image_list:
        image = Image.open(BytesIO(image_bytes))
        raw_text = image_to_string(image,lang='eng+jpn+chi_sim+chi_tra')
        print(raw_text)
        image_content.append(raw_text)
    
    return "\n".join(image_content)

# def extract_text_from_pdf(pdf_path):
#     text = ""
#     with open(pdf_path, "rb") as file:
#         reader = PyPDF2.PdfReader(file)
#         for page_num in range(len(reader.pages)):
#             page = reader.pages[page_num]
#             text += page.extract_text() or ""
            
#     return text

# def query_text(text, query):
#     # Load a pre-trained question-answering model
#     nlp = pipeline("question-answering", model="distilbert-base-uncased-distilled-squad")

#     # Perform the query
#     result = nlp(question=query, context=text)
#     return result['answer']

def query_text(text,query):
    response = model.generate_content("Remember the following data : \'"+text+"\'.Now, "+query+". Just tell the answer.")
    print(response.text)
    return response.text


def main(pdf_path, query):
    if not os.path.exists(pdf_path):
        print(f"File not found: {pdf_path}")
        sys.exit(1)

    images = convert_pdf_to_images(pdf_path)
    text = extract_text_with_pytesseract(images)
    
    response = model.generate_content(f'Format the string: "{text}" into headers and corresponding values of rows and columns so that this could be converted into a .csv file using pythons CSV library. Also don\'t include any explanation')
    
    comma_separated_string = response.text
    lines = comma_separated_string.split('\n')
    csv_path = pdf_path.replace('.pdf', '.csv')
    print("------"+csv_path)

    with open(csv_path, 'w', newline='',  encoding='utf-8') as csvfile:
        csv_writer = csv.writer(csvfile)
        for line in lines:
            row = line.split(',')
            csv_writer.writerow(row)
    
    pdf_text = text
    
    if not pdf_text.strip():
        print("No text extracted from the PDF.")
        return
    
    answer = query_text(pdf_text, query)
    # print(answer)
    
    print(f"CSV file created at: {csv_path}")
    return answer, csv_path

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: python script.py <pdf_path> <query>")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    query = sys.argv[2]

    answer, csv_path = main(pdf_path, query)
    print(f"Query Answer: {answer}")
