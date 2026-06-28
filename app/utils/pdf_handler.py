import os
from pypdf import PdfReader, PdfWriter

def get_pdf_fields(pdf_path):
    """Liest alle interaktiven Formularfelder aus einer PDF-Datei aus."""
    if not os.path.exists(pdf_path):
        return {}
    
    reader = PdfReader(pdf_path)
    fields = reader.get_fields()
    
    if not fields:
        return {}
        
    # Extrahiere Feldnamen und Typen (Text, Checkbox etc.)
    form_fields = {}
    for name, field in fields.items():
        field_type = field.get('/FT', '/Unknown')
        form_fields[name] = {
            'type': str(field_type),
            'value': field.get('/V', '')
        }
    return form_fields

def fill_pdf_form(source_pdf, output_pdf, data_dict):
    """Befüllt die Formularfelder einer PDF und speichert sie ab."""
    reader = PdfReader(source_pdf)
    writer = PdfWriter()
    
    # Kopiere Seiten und befülle Felder
    writer.append(reader)
    
    # pypdf benötigt das Mapping auf der Root/Page-Ebene
    writer.update_page_form_field_values(writer.pages[0], data_dict)
    
    # Bei mehrseitigen Dokumenten sicherheitshalber alle Seiten updaten
    for page in writer.pages:
        writer.update_page_form_field_values(page, data_dict)

    with open(output_pdf, "wb") as output_file:
        writer.write(output_file)
        
    return True
