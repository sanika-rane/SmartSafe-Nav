from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "IEEE_SUBMISSION_READINESS_CHECKLIST.docx"


def shade_cell(cell, fill):
    properties = cell._tc.get_or_add_tcPr()
    shading = OxmlElement("w:shd")
    shading.set(qn("w:fill"), fill)
    properties.append(shading)


def set_cell_text(cell, text, bold=False, color=None):
    cell.text = ""
    paragraph = cell.paragraphs[0]
    run = paragraph.add_run(str(text))
    run.bold = bold
    if color:
        run.font.color.rgb = RGBColor(*color)
    cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER


def add_table(document, headers, rows, widths=None):
    table = document.add_table(rows=1, cols=len(headers))
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    for index, header in enumerate(headers):
        set_cell_text(table.rows[0].cells[index], header, bold=True, color=(255, 255, 255))
        shade_cell(table.rows[0].cells[index], "1F4E79")
    for row in rows:
        cells = table.add_row().cells
        for index, value in enumerate(row):
            set_cell_text(cells[index], value)
            if index == 1 and str(value).startswith("TO BE"):
                shade_cell(cells[index], "FFF2CC")
            elif index == 1 and str(value) in {"Complete", "Implemented", "Identified"}:
                shade_cell(cells[index], "E2F0D9")
    if widths:
        for row in table.rows:
            for index, width in enumerate(widths):
                row.cells[index].width = Inches(width)
    document.add_paragraph()
    return table


def add_bullets(document, items):
    for item in items:
        document.add_paragraph(item, style="List Bullet")


def add_numbered(document, items):
    for item in items:
        document.add_paragraph(item, style="List Number")


def add_status_section(document, title, status, body, actions=None):
    document.add_heading(title, level=2)
    paragraph = document.add_paragraph()
    run = paragraph.add_run(f"Status: {status}")
    run.bold = True
    if status.startswith("TO BE"):
        run.font.color.rgb = RGBColor(156, 101, 0)
    elif status in {"Complete", "Implemented", "Identified"}:
        run.font.color.rgb = RGBColor(0, 97, 0)
    document.add_paragraph(body)
    if actions:
        document.add_paragraph("Required evidence or action:", style="Heading 3")
        add_bullets(document, actions)


doc = Document()
section = doc.sections[0]
section.top_margin = Inches(0.7)
section.bottom_margin = Inches(0.7)
section.left_margin = Inches(0.8)
section.right_margin = Inches(0.8)

styles = doc.styles
styles["Normal"].font.name = "Aptos"
styles["Normal"].font.size = Pt(10)
styles["Title"].font.name = "Aptos Display"
styles["Title"].font.size = Pt(25)
styles["Heading 1"].font.name = "Aptos Display"
styles["Heading 1"].font.color.rgb = RGBColor(31, 78, 121)
styles["Heading 2"].font.name = "Aptos Display"
styles["Heading 2"].font.color.rgb = RGBColor(31, 78, 121)

# Title page
paragraph = doc.add_paragraph()
paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
paragraph.add_run("IEEE SUBMISSION-READINESS CHECKLIST").bold = True
paragraph.runs[0].font.size = Pt(24)
paragraph.runs[0].font.color.rgb = RGBColor(31, 78, 121)

paragraph = doc.add_paragraph()
paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = paragraph.add_run("SafePath AI: Smart Navigation for Women's Safety")
run.bold = True
run.font.size = Pt(17)

paragraph = doc.add_paragraph()
paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
paragraph.add_run("Project evidence review and completion plan\nSeptember 22, 2026")

doc.add_paragraph()
paragraph = doc.add_paragraph()
paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
paragraph.add_run("Purpose: identify what is already supported by the project and what must be added before IEEE submission.")

doc.add_page_break()

# Executive summary
doc.add_heading("1. Executive Summary", level=1)
doc.add_paragraph(
    "SafePath AI is a prototype that obtains driving-route alternatives from OSRM, evaluates sampled route points with a LightGBM safety classifier and rule-based safety factors, and presents ranked routes in a React and Leaflet interface. The project has a strong implementation foundation, but the paper still needs reproducible experimental evidence, publication-quality figures and tables, verified references, and final IEEE formatting."
)
doc.add_paragraph(
    "The most important reporting limitation is that the dataset is synthetic. The reported model scores demonstrate technical feasibility on the available split; they do not establish real-world safety performance. The paper should also describe the system accurately as a route-alternative ranking system, not as a complete safety-weighted road-graph optimizer."
)

doc.add_heading("2. Checklist Status Overview", level=1)
status_rows = [
    ("Six-author IEEE block", "TO BE COMPLETED", "Add six verified author identities, affiliations, and emails."),
    ("Exact title", "Complete", "Project title is available."),
    ("Abstract", "Complete", "Content exists; proofread for IEEE length and claims."),
    ("Keywords", "Complete", "Content exists; align with final paper terminology."),
    ("Introduction", "Complete", "Content exists; verify citations."),
    ("Related work", "Citations required", "Add verified IEEE references."),
    ("Problem statement", "Complete", "Content exists."),
    ("System architecture", "Complete", "Architecture is documented; add an actual diagram."),
    ("Methodology", "Complete", "Pipeline is documented; add equations and citations."),
    ("Implementation", "Complete", "Backend, frontend, model, and integration are implemented."),
    ("Dataset details", "TO BE ADDED", "Add dataset statistics, feature definitions, provenance, and limitations."),
    ("Experimental setup", "TO BE ADDED", "Add exact preprocessing, split, parameters, environment, and commands."),
    ("Numerical results", "TO BE ADDED", "Add complete numeric model comparison and route-level results."),
    ("Model metrics", "TO BE ADDED", "Add per-class metrics, confusion matrix, ROC-AUC, and unsafe recall."),
    ("Hardware/software configuration", "TO BE ADDED", "Record the actual training and inference environment."),
    ("Figures", "Need actual diagrams", "Create architecture, pipeline, route flow, confusion matrix, and screenshots."),
    ("Tables", "Partially prepared", "Convert project facts into numbered IEEE tables."),
    ("References", "REFERENCES TO BE ADDED", "Add and verify citations for methods, tools, and related work."),
    ("Security/privacy discussion", "Complete", "Keep and connect to the safety-sensitive use case."),
    ("Limitations", "Complete", "Emphasize synthetic data, route sampling, and provider dependence."),
    ("Future work", "Complete", "Include graph routing, real data, calibration, and deployment."),
    ("Technical inconsistencies", "Identified", "Resolve terminology and claims before submission."),
    ("Citation verification", "Required", "Check every citation against a reliable source."),
    ("IEEE template formatting", "Required before final submission", "Apply official IEEE template and two-column rules."),
    ("Final proofreading", "Required", "Perform technical, language, figure, and reference checks."),
    ("Reproducibility verification", "Required", "Run from a clean environment and record outputs."),
]
add_table(doc, ["Requirement", "Status", "Meaning / next action"], status_rows, [2.1, 1.5, 3.3])

# Dataset
doc.add_heading("3. Dataset Details - TO BE ADDED", level=1)
doc.add_paragraph("The project currently provides enough information to write a factual dataset subsection, but the paper needs a formal data dictionary and provenance statement.")
add_table(doc, ["Dataset item", "Verified value"], [
    ("File", "data/Synthetic_Dataset.csv"),
    ("Records", "30,000"),
    ("Original columns", "32"),
    ("Encoded model features", "113"),
    ("Training/testing split", "24,000 / 6,000 records (80/20)"),
    ("Source locations", "35"),
    ("Destination locations", "35"),
    ("Hour range", "0-23"),
    ("Target classes", "Moderate, Safe, Unsafe"),
    ("Data type", "Synthetic"),
], [2.5, 4.4])
doc.add_paragraph("Class distribution:")
add_table(doc, ["Class", "Full dataset", "Training set", "Test set"], [
    ("Safe", "24,917", "19,934", "4,983"),
    ("Moderate", "4,290", "3,432", "858"),
    ("Unsafe", "793", "634", "159"),
], [2.0, 1.5, 1.5, 1.5])
doc.add_paragraph("Add the following to the paper:")
add_bullets(doc, [
    "A data dictionary with field meanings, units, allowed categorical values, and target definition.",
    "The synthetic-data generation method and assumptions.",
    "The method used to derive Safety_Score and Safety_Level.",
    "A statement that synthetic data cannot validate real-world safety performance.",
    "A discussion of class imbalance, repeated route pairs, and possible location memorization.",
])

# Experimental setup
doc.add_heading("4. Experimental Setup - TO BE ADDED", level=1)
doc.add_paragraph("The notebooks establish the main pipeline, but the paper must report the exact configuration used to produce the saved artifacts.")
add_numbered(doc, [
    "Remove duplicate records.",
    "Use Safety_Level as the target and remove Safety_Score from model inputs.",
    "Convert Boolean fields to integers.",
    "One-hot encode categorical fields.",
    "Label-encode Moderate, Safe, and Unsafe as 0, 1, and 2.",
    "Standardize predictors with StandardScaler.",
    "Use an 80/20 stratified train/test split with random_state=42.",
    "Compare Decision Tree, Random Forest, XGBoost, and LightGBM.",
    "Save the LightGBM model, scaler, and label encoder as runtime artifacts.",
])
doc.add_paragraph("Still required: exact Python/package versions, full LightGBM parameters, CPU/GPU setting, training duration, inference latency, and whether hyperparameter tuning or early stopping was used.")

# Results and metrics
doc.add_heading("5. Numerical Results and Model Metrics - TO BE ADDED", level=1)
doc.add_paragraph("The project already contains initial model-comparison values. The paper must add complete per-class metrics and publication-quality tables.")
add_table(doc, ["Model", "Accuracy"], [
    ("Decision Tree", "95.90%"),
    ("Random Forest", "96.32%"),
    ("XGBoost", "97.38%"),
    ("LightGBM", "97.47%"),
], [3.2, 2.0])
doc.add_paragraph("Known LightGBM results:")
add_table(doc, ["Metric", "Value"], [
    ("Accuracy", "0.9746666667"),
    ("Weighted precision", "0.9747597599"),
    ("Weighted recall", "0.9746666667"),
    ("Weighted F1-score", "0.9746692316"),
], [3.2, 2.0])
doc.add_paragraph("Required additional results:")
add_bullets(doc, [
    "Per-class precision, recall, and F1-score.",
    "Macro-average precision, recall, and F1-score.",
    "Confusion matrix with class labels.",
    "Multiclass ROC-AUC.",
    "Unsafe-class recall and false-negative count.",
    "Route-level scoring examples and explanation outputs.",
])
doc.add_paragraph("Because Unsafe represents only 2.6% of the full dataset, accuracy must not be the only headline metric. Unsafe recall and false negatives are especially important for this application.")

# Hardware/software
doc.add_heading("6. Hardware and Software Configuration - TO BE ADDED", level=1)
doc.add_paragraph("These values must be measured from the machine used for training and testing. They should not be guessed.")
add_table(doc, ["Item", "Value to record"], [
    ("Operating system", "Windows version and architecture"),
    ("CPU", "Processor model and core count"),
    ("RAM", "Installed memory"),
    ("GPU", "Model or Not used"),
    ("Python", "Exact version"),
    ("ML packages", "Exact installed versions"),
    ("Frontend packages", "React, Vite, Leaflet versions"),
    ("Training time", "Measured duration"),
    ("Inference time", "Measured route prediction latency"),
    ("Artifact versions", "Dataset/model hashes and creation date"),
], [2.4, 4.5])

# Figures and tables
doc.add_heading("7. Figures - Need Actual Diagrams", level=1)
doc.add_paragraph("The paper currently has implementation descriptions, but IEEE submission requires actual numbered figures.")
add_numbered(doc, [
    "System architecture: React frontend, Flask API, OSRM, dataset, model artifacts, scoring, and explainability.",
    "Machine-learning pipeline: cleaning, encoding, scaling, splitting, training, evaluation, and artifact export.",
    "Runtime route-selection flow: route alternatives, sampling, nearest records, prediction, hybrid score, explanation, and ranking.",
    "Frontend screenshot showing the map, route alternatives, scores, and explanation panel.",
    "LightGBM confusion matrix.",
    "Model comparison chart.",
    "Explainable-AI output showing positive and negative route factors.",
])

doc.add_heading("8. Tables - Partially Prepared", level=1)
add_bullets(doc, [
    "Dataset feature-category table.",
    "Class-distribution table.",
    "Model comparison table with complete metrics.",
    "Hardware and software configuration table.",
    "API endpoint table.",
    "Rule-based safety-factor table showing positive and negative conditions.",
])

# References
doc.add_heading("9. References - TO BE ADDED", level=1)
doc.add_paragraph("Add verified IEEE-style citations for both the research context and the technical methods used in the project.")
add_bullets(doc, [
    "LightGBM research paper.",
    "SHAP research paper.",
    "Scikit-learn documentation or relevant method references.",
    "XGBoost research paper, if XGBoost comparison is reported.",
    "OSRM and OpenStreetMap official sources.",
    "Research on safe-route recommendation and women’s urban safety.",
    "Research on imbalanced classification and probability calibration.",
])
doc.add_paragraph("Verify authors, title, venue, year, pages, DOI or official URL, and access date. Do not add unverified or invented citations.")

# Other checklist areas
doc.add_heading("10. Completed and Required Final Checks", level=1)
add_status_section(doc, "Six-author IEEE block", "TO BE COMPLETED", "The codebase cannot provide author identities. Add the exact six-author order, affiliations, institutions, locations, and professional email addresses.")
add_status_section(doc, "Technical inconsistencies", "Identified", "Describe the system as ranking OSRM route alternatives with a hybrid safety score. Do not describe it as a complete safety-weighted graph optimizer.")
add_status_section(doc, "Citation verification", "Required", "Check that every in-text citation exists in the reference list and every listed reference is used.")
add_status_section(doc, "IEEE template formatting", "Required before final submission", "Apply the official IEEE template, two-column layout, author block, figure captions, table captions, equations, margins, font rules, and page limits.")
add_status_section(doc, "Final proofreading", "Required", "Check terminology, units, abbreviations, claims, figure/table references, grammar, and safety disclaimers.")
add_status_section(doc, "Reproducibility verification", "Required", "Run the backend and frontend from a clean environment, rerun evaluation, verify route scoring and explanations, and record all commands and outputs.")

# Reproducibility
doc.add_heading("11. Reproducibility Checklist", level=1)
add_numbered(doc, [
    "Create a clean Python environment and install Backend/requirements.txt.",
    "Verify the dataset and model artifact files are present.",
    "Run the backend health endpoint.",
    "Install frontend dependencies and start Vite.",
    "Load locations and request a route.",
    "Confirm route scores and explanations render.",
    "Run model evaluation using the recorded random seed.",
    "Record Python, package, hardware, dataset, and artifact versions.",
    "Save the final metrics, confusion matrix, figures, and tables.",
])

# Priority plan
doc.add_heading("12. Highest-Priority Action Plan", level=1)
add_numbered(doc, [
    "Generate complete per-class LightGBM metrics, confusion matrix, and ROC-AUC.",
    "Record the actual hardware and software environment.",
    "Create the architecture, ML pipeline, runtime flow, and explainability diagrams.",
    "Prepare the dataset, class-distribution, model-comparison, and environment tables.",
    "Add verified IEEE references.",
    "Demonstrate one selected route with its explainable-AI rationale.",
    "Run the project from a clean environment and verify reproducibility.",
    "Apply the official IEEE template and perform final proofreading.",
])

# Closing note
doc.add_heading("13. Final Assessment", level=1)
doc.add_paragraph(
    "The project is suitable for an IEEE-style prototype or feasibility paper after the missing evidence is added. The strongest current contributions are the hybrid safety-scoring design, route-alternative comparison, map-based interface, and explainable-AI prototype integration. The paper must remain transparent about the synthetic dataset, class imbalance, external routing dependency, route sampling, and the distinction between predicted safety and guaranteed safety."
)

# Footer
for section in doc.sections:
    footer = section.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    footer.add_run("SafePath AI - IEEE Submission Readiness Checklist")


doc.save(OUTPUT)
print(OUTPUT)
