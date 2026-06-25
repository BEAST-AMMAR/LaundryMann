from fpdf import FPDF
import datetime
import os

class CareGuidePDF(FPDF):
    def header(self):
        # Header setup
        self.set_font('Arial', 'B', 15)
        self.set_fill_color(16, 17, 20) # Dark Charcoal
        self.set_text_color(240, 240, 242)
        self.cell(0, 15, ' NEXUS Laundry AI - Care Guide', 0, 1, 'C', fill=True)
        self.ln(5)

    def footer(self):
        # Footer setup
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(100, 100, 100)
        self.cell(0, 10, f'Generated on {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")} | Page {self.page_no()}', 0, 0, 'C')

def generate_care_pdf(color: str, fabric: str, stains: str, instructions: str, output_path: str = "care_guide.pdf"):
    pdf = CareGuidePDF()
    pdf.add_page()
    
    # Body
    pdf.set_font('Arial', 'B', 12)
    pdf.set_text_color(0, 0, 0)
    
    pdf.cell(0, 10, 'Garment Analysis Summary', 0, 1, 'L')
    pdf.set_font('Arial', '', 11)
    
    pdf.cell(0, 8, f"Detected Color: {color}", 0, 1, 'L')
    pdf.cell(0, 8, f"Detected Fabric: {fabric}", 0, 1, 'L')
    pdf.cell(0, 8, f"Stain Status: {stains}", 0, 1, 'L')
    
    pdf.ln(10)
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, 'Washing Instructions', 0, 1, 'L')
    
    pdf.set_font('Arial', '', 11)
    # instructions can be long, so use multi_cell
    pdf.multi_cell(0, 8, instructions.replace('*', ''))
    
    # Save the PDF
    pdf.output(output_path)
    return output_path
