import argparse
import fitz  # PyMuPDF

'''
You can run this script from the command line as follows:
python3 extract_text.py --input sample_input_text.pdf --output sample_output.txt
'''

def extract_text_from_pdf(pdf_path, output_txt_path):
    try:
        # Open the PDF file
        pdf_document = fitz.open(pdf_path)

        # Initialize an empty string to store the extracted text
        extracted_text = ""

        # Loop through each page in the PDF
        for page_num in range(len(pdf_document)):
            page = pdf_document[page_num]
            extracted_text += page.get_text() + "\n"  # Extract text and add a newline for separation

        # Close the PDF document
        pdf_document.close()

        # Write the extracted text to a .txt file
        with open(output_txt_path, 'w', encoding='utf-8') as txt_file:
            txt_file.write(extracted_text)

        print(f"Text successfully extracted and saved to {output_txt_path}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Extract text from a PDF file.')
    parser.add_argument('--input', type=str, required=True, help='Input PDF file path')
    parser.add_argument('--output', type=str, required=True, help='Output text file path')
    args = parser.parse_args()

    # Call the function to extract text and save it
    extract_text_from_pdf(args.input, args.output)