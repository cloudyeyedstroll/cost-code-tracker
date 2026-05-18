from fpdf import FPDF
import io
import datetime
import database as db

class PDFReport(FPDF):
    def __init__(self, project_data, report_date, logo_bytes=None):
        super().__init__()
        self.project_data = project_data
        self.report_date = report_date
        self.logo_bytes = logo_bytes

    def header(self):
        # Render dynamic logo if available
        if self.logo_bytes:
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                tmp.write(self.logo_bytes)
                tmp_path = tmp.name
            
            # Center the image: (210mm page width - 40mm image width) / 2 = 85
            self.image(tmp_path, x=85, y=8, w=40)
            self.ln(25) # push down text
        else:
            self.ln(10)
        
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, 'Supervisor Daily Report', 0, 1, 'C')
        
        self.set_font('Arial', '', 12)
        project_name = self.project_data['project_name'] if self.project_data else 'N/A'
        self.cell(0, 10, f'Project: {project_name} | Date: {self.report_date}', 0, 1, 'C')
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.line(10, self.get_y(), 200, self.get_y())
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def build_daily_pdf_buffer(project_id, selection_date):
    data = db.get_daily_report_data(project_id, selection_date)
    if not data:
        return None
        
    # Check if there are NO logs
    if not data.get('labor_logs') and not data.get('equipment_logs') and not data.get('material_logs') and not data.get('subcontractor_logs'):
        return None
    
    logo_bytes = db.get_company_logo()
    
    pdf = PDFReport(data['project'], selection_date, logo_bytes)
    pdf.add_page()
    
    # 1. Crew Resources (Labor Logs)
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, '1. Crew Resources', 0, 1)
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(40, 8, 'Employee', 1)
    pdf.cell(40, 8, 'Role', 1)
    pdf.cell(80, 8, 'Cost Code', 1)
    pdf.cell(30, 8, 'Hours', 1)
    pdf.ln()
    
    pdf.set_font('Arial', '', 10)
    for row in data.get('labor_logs', []):
        emp = row.get('employees', {}) or {}
        emp_name = f"{emp.get('first_name', '')} {emp.get('last_name', '')}".strip()
        role = emp.get('role', 'N/A')
        
        cc = row.get('cost_codes', {}) or {}
        code = cc.get('code', 'N/A')
        desc = cc.get('description', '')
        cc_str = f"{code} - {desc}"[:40]
        
        hrs = str(row.get('hours_worked', '0'))
        
        pdf.cell(40, 8, emp_name[:20], 1)
        pdf.cell(40, 8, role[:20], 1)
        pdf.cell(80, 8, cc_str, 1)
        pdf.cell(30, 8, hrs, 1)
        pdf.ln()
    
    pdf.ln(5)
    
    # 2. Fleet Utilization (Equipment Logs)
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, '2. Fleet Utilization', 0, 1)
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(60, 8, 'Equipment Unit', 1)
    pdf.cell(100, 8, 'Cost Code', 1)
    pdf.cell(30, 8, 'Hours', 1)
    pdf.ln()
    
    pdf.set_font('Arial', '', 10)
    for row in data.get('equipment_logs', []):
        eq = row.get('equipment', {}) or {}
        unit = eq.get('unit_number', 'N/A')
        
        cc = row.get('cost_codes', {}) or {}
        code = cc.get('code', 'N/A')
        desc = cc.get('description', '')
        cc_str = f"{code} - {desc}"[:50]
        
        hrs = str(row.get('hours_used', '0'))
        
        pdf.cell(60, 8, unit[:30], 1)
        pdf.cell(100, 8, cc_str, 1)
        pdf.cell(30, 8, hrs, 1)
        pdf.ln()
        
    # 3. Materials & Yields
    if data.get('material_logs'):
        pdf.ln(5)
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, '3. Materials & Yields', 0, 1)
        pdf.set_font('Arial', 'B', 10)
        pdf.cell(30, 8, 'Type', 1)
        pdf.cell(40, 8, 'Supplier', 1)
        pdf.cell(50, 8, 'Description', 1)
        pdf.cell(40, 8, 'Cost Code', 1)
        pdf.cell(30, 8, 'Quantity', 1)
        pdf.ln()
        
        pdf.set_font('Arial', '', 10)
        for row in data['material_logs']:
            l_type = str(row.get('log_type', 'N/A'))
            supp = str(row.get('supplier', 'N/A'))
            desc = str(row.get('material_description', ''))
            
            cc = row.get('cost_codes', {}) or {}
            cc_str = f"{cc.get('code', 'N/A')} - {cc.get('description', '')}"[:25]
            
            qty = f"{row.get('quantity', '0')} {row.get('unit', '')}"
            
            pdf.cell(30, 8, l_type[:15], 1)
            pdf.cell(40, 8, supp[:20], 1)
            pdf.cell(50, 8, desc[:25], 1)
            pdf.cell(40, 8, cc_str, 1)
            pdf.cell(30, 8, qty, 1)
            pdf.ln()

    # 4. Subcontractors
    if data.get('subcontractor_logs'):
        pdf.ln(5)
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, '4. Subcontractors', 0, 1)
        pdf.set_font('Arial', 'B', 10)
        pdf.cell(45, 8, 'Company', 1)
        pdf.cell(50, 8, 'Scope of Work', 1)
        pdf.cell(45, 8, 'Cost Code', 1)
        pdf.cell(30, 8, 'Ticket #', 1)
        pdf.cell(20, 8, 'Hrs', 1)
        pdf.ln()
        
        pdf.set_font('Arial', '', 10)
        for row in data['subcontractor_logs']:
            comp = str(row.get('company_name', 'N/A'))
            scope = str(row.get('scope_of_work', 'N/A'))
            
            cc = row.get('cost_codes', {}) or {}
            cc_str = f"{cc.get('code', 'N/A')} - {cc.get('description', '')}"[:20]
            
            tno = str(row.get('ticket_number') or 'N/A')
            hrs = str(row.get('hours_worked', '0'))
            
            pdf.cell(45, 8, comp[:22], 1)
            pdf.cell(50, 8, scope[:25], 1)
            pdf.cell(45, 8, cc_str, 1)
            pdf.cell(30, 8, tno[:15], 1)
            pdf.cell(20, 8, hrs, 1)
            pdf.ln()

    buffer = io.BytesIO()
    # output(dest='S') returns a bytes string in fpdf2, we just write to BytesIO
    pdf_bytes = pdf.output(dest='S')
    buffer.write(pdf_bytes)
    buffer.seek(0)
    return buffer
