from fpdf import FPDF
from PIL import Image
import os
import threading
import string

def images_to_pdf(image_paths, output_pdf, title=None, user_answers=None, grade=0):
    def thread_function():
        nonlocal image_paths, output_pdf, title, user_answers
        pdf = FPDF(unit='pt')  # Initialize FPDF with points (pt) as the unit

        if title:
            pdf.set_title(title)  # Set the PDF title
            pdf.add_page()  # Add a cover page
            pdf.set_font("Arial", size=24, style="B")  # Set font for the title
            pdf.cell(0, 100, title, align="C", ln=True)  # Add the title text at the top
            pdf.ln(200)  # Add some spacing
            pdf.cell(0, 10, "Eyefollow Results!", align="C", ln=True)

        # Define the page dimensions (A4 size in points: 595 x 842)
        page_width, page_height = 595.0, 842.0

        for image_path in image_paths:
            image = Image.open(image_path)
            img_width, img_height = image.size

            # Calculate aspect ratio and scaling
            img_aspect = img_width / img_height
            page_aspect = page_width / page_height

            if img_aspect > page_aspect:
                # Image is wider than the page; fit by width
                scaled_width = page_width
                scaled_height = scaled_width / img_aspect
            else:
                # Image is taller than the page; fit by height
                scaled_height = page_height
                scaled_width = scaled_height * img_aspect

            # Add a new page and place the image
            pdf.add_page()
            pdf.image(image_path, x=(page_width - scaled_width) / 2, y=(page_height - scaled_height) / 2, w=scaled_width, h=scaled_height)

        if len(user_answers) > 0:
            # grade_data = get_grade_data(grade)
            grade_data = None
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            score = 0
            for i, (question, user_answer) in enumerate(zip(grade_data.questions, user_answers), 1):
                pdf.multi_cell(0, 10, f"{i}) {question['message']}")
                for letter, option in zip(string.ascii_lowercase, question['options']):
                    pdf.multi_cell(0, 10, f"\n\t\t{letter}) {option}")
                pdf.multi_cell(0, 10, f"\nUser Answer: {user_answer}\n")
                pdf.ln(5)
                pdf.multi_cell(0, 10, f"Correct Answer: {question['answer']}\n")
                if user_answer == question['answer']:
                    score += 1
                pdf.ln(10)
            pdf.ln(20)
            pdf.cell(0, 10, f"Score: {score} out of {len(grade_data.questions)}", align="C")

        try:
            pdf.output(output_pdf)
            print(f"PDF saved as {output_pdf}")
        except PermissionError:
            print(f"Error: Cannot write to {output_pdf}. The file might be open or not writable.")
            print("Please close the file if it's open, or check the file permissions.")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
    
    # Run the conversion in a separate thread
    thread = threading.Thread(target=thread_function)
    thread.start()
