import httpx
import os
import io
from pathlib import Path
from django.shortcuts import render, redirect
from django.http import FileResponse
from django.contrib.auth.decorators import login_required
from dotenv import load_dotenv
from users.models import Profile

# ReportLab (PDF)
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Image as RLImage, FrameBreak, Flowable
from reportlab.graphics.shapes import Drawing, Line
from reportlab.lib.units import mm
from PIL import Image, ImageOps, ImageDraw

# --- ЗАГРУЗКА ENV ---
BASE_DIR = Path(__file__).resolve().parent.parent
env_path = BASE_DIR / '.env'
load_dotenv(dotenv_path=env_path)

# --- КЛАСС ДЛЯ ПОЛОСКИ СКИЛЛОВ (PRO) ---
class ProSkillBar(Flowable):
    def __init__(self, name, level_percent, width=150, height=14):
        Flowable.__init__(self)
        self.name = name
        self.level = level_percent / 100.0
        self.width = width
        self.height = height
        
        if self.level >= 0.9: self.txt = "EXPERT"
        elif self.level >= 0.70: self.txt = "SENIOR"
        elif self.level >= 0.40: self.txt = "MIDDLE"
        else: self.txt = "JUNIOR"

    def draw(self):
        c = self.canv
        # Текст (Имя)
        c.setFont("Helvetica-Bold", 10)
        c.setFillColor(colors.white)
        c.drawString(0, 7, self.name)
        
        # Текст (Уровень)
        c.setFont("Helvetica", 8)
        c.setFillColor(colors.HexColor("#bdc3c7"))
        c.drawRightString(self.width, 7, self.txt)
        
        # Фон полоски
        c.setFillColor(colors.HexColor("#34495e"))
        c.roundRect(0, 0, self.width, 4, 2, fill=1, stroke=0)
        
        # Активная полоска (Cyan)
        c.setFillColor(colors.HexColor("#4cc9f0")) 
        c.roundRect(0, 0, self.width * self.level, 4, 2, fill=1, stroke=0)

@login_required(login_url='login') 
def home(request):
    result = None
    error_message = None
    profile, created = Profile.objects.get_or_create(user=request.user)
    if created: profile.save()

    if request.method == "POST":
        action = request.POST.get('action')

        # === 1. ГЕНЕРАЦИЯ AI (ELITE MODE) ===
        if action == 'generate_letter':
            resume_text = request.POST.get('resume')
            job_desc = request.POST.get('job_description')
            
            # Новые поля
            company_name = request.POST.get('company_name', 'Target Company')
            job_title = request.POST.get('job_title_ai', 'Professional')
            tone = request.POST.get('tone', 'Professional')
            language = request.POST.get('language', 'English')

            api_key = os.getenv("GROQ_API_KEY")
            
            if not api_key: 
                error_message = "API Key not found in .env!"
            elif profile.generations_count <= 0 and not profile.is_premium: 
                error_message = "У вас закончились бесплатные генерации! Купите Premium."
            else:
                try:
                    # 🔥 ТОТ САМЫЙ ЭЛИТНЫЙ ПРОМПТ 🔥
                    system_prompt = """
You are an elite career strategist, senior recruiter, ATS optimization expert,
and professional cover letter writer with experience hiring for top global
companies (FAANG, startups, enterprise, and tech firms).

Your goal is NOT to simply write a cover letter.
Your goal is to maximize the candidate’s chances of getting an interview.

STRUCTURE YOUR RESPONSE EXACTLY LIKE THIS:
1. MAIN COVER LETTER
2. VERSION A (Corporate/Traditional)
3. VERSION B (Bold/Impact)
4. ATS ANALYSIS (Score 0-100 & Tips)
5. RECRUITER RISK ANALYSIS (3 risks & fixes)

Do not include any conversational filler before or after.
"""
                    
                    user_prompt = f"""
========================
INPUT DATA
========================
Candidate CV: {resume_text}
Job Description: {job_desc}
Target Company: {company_name}
Job Title: {job_title}
Preferred Tone: {tone}
Language: {language}

Generate the elite response now.
"""

                    headers = {
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    }
                    data = {
                        "model": "llama-3.1-8b-instant",
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        "temperature": 0.7 
                    }
                    
                    resp = httpx.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=data, timeout=60)
                    
                    if resp.status_code == 200:
                        result = resp.json()['choices'][0]['message']['content']
                        # Списываем попытку
                        if not profile.is_premium: 
                            profile.generations_count -= 1
                            profile.save()
                    else: 
                        error_message = f"API Error: {resp.text}"

                except Exception as e: 
                    error_message = f"Connection Error: {str(e)}"

        # === 2. СКАЧИВАНИЕ PDF ===
        elif action == 'download_pdf':
            return generate_pdf(request)

    return render(request, 'generator/home.html', {
        'result': result, 
        'error_message': error_message,
        'resume_text': request.POST.get('resume', '')
    })

# === PDF GENERATOR (NAVY PRO STYLE) ===
def generate_pdf(request):
    buffer = io.BytesIO()
    doc = BaseDocTemplate(buffer, pagesize=A4, rightMargin=0, leftMargin=0, topMargin=0, bottomMargin=0)

    # ЦВЕТА
    C_SIDEBAR = colors.HexColor("#2c3e50") # Navy Blue
    C_ACCENT  = colors.HexColor("#4cc9f0") # Cyber Cyan
    C_TEXT    = colors.HexColor("#2c3e50")
    C_GREY    = colors.HexColor("#7f8c8d")

    def draw_bg(canvas, doc):
        canvas.saveState()
        canvas.setFillColor(C_SIDEBAR)
        canvas.rect(0, 0, 80*mm, 297*mm, fill=1, stroke=0) # Sidebar 80mm
        canvas.restoreState()

    frame_sb = Frame(0, 0, 80*mm, 297*mm, id='sb', leftPadding=20, rightPadding=20, topPadding=30, bottomPadding=30)
    frame_main = Frame(80*mm, 0, 130*mm, 297*mm, id='main', leftPadding=25, rightPadding=25, topPadding=30, bottomPadding=30)
    doc.addPageTemplates([PageTemplate(id='Layout', frames=[frame_sb, frame_main], onPage=draw_bg)])

    styles = getSampleStyleSheet()
    
    # Styles Sidebar
    s_sb_h = ParagraphStyle('SB_H', fontName='Helvetica-Bold', fontSize=12, textColor=C_ACCENT, spaceBefore=20, spaceAfter=8, textTransform='uppercase')
    s_sb_t = ParagraphStyle('SB_T', fontName='Helvetica', fontSize=9.5, textColor=colors.white, leading=14)
    s_sb_l = ParagraphStyle('SB_L', fontName='Helvetica-Bold', fontSize=8, textColor=colors.HexColor("#bdc3c7"), spaceBefore=6)

    # Styles Main
    s_name = ParagraphStyle('Name', fontName='Helvetica-Bold', fontSize=32, textColor=C_TEXT, leading=34, spaceAfter=5)
    s_role = ParagraphStyle('Role', fontName='Helvetica-Bold', fontSize=14, textColor=C_ACCENT, textTransform='uppercase', spaceAfter=20)
    s_h2 = ParagraphStyle('H2', fontName='Helvetica-Bold', fontSize=13, textColor=C_TEXT, spaceBefore=18, spaceAfter=8, textTransform='uppercase')
    s_body = ParagraphStyle('Body', fontName='Helvetica', fontSize=10.5, textColor=colors.HexColor("#34495e"), leading=16, spaceAfter=8)

    story = []

    # --- 1. SIDEBAR ---
    photo = request.FILES.get('photo')
    if photo:
        try:
            img = Image.open(photo).convert("RGB")
            mask = Image.new('L', (500, 500), 0)
            draw = ImageDraw.Draw(mask)
            draw.ellipse((0, 0, 500, 500), fill=255)
            output = ImageOps.fit(img, (500, 500), centering=(0.5, 0.5))
            output.putalpha(mask)
            
            import tempfile
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
            output.save(tmp, format='PNG')
            tmp.close()
            story.append(RLImage(tmp.name, width=50*mm, height=50*mm))
            story.append(Spacer(1, 20))
        except: pass

    story.append(Paragraph("CONTACTS", s_sb_h))
    
    # Собираем контакты
    contacts = [
        ("LOCATION", request.POST.get('location')),
        ("EMAIL", request.POST.get('email')),
        ("PHONE", request.POST.get('phone')),
        ("LINKEDIN", request.POST.get('linkedin')),
    ]
    
    for lbl, val in contacts:
        if val:
            story.append(Paragraph(lbl, s_sb_l))
            story.append(Paragraph(val, s_sb_t))
            story.append(Spacer(1, 2))

    # Скиллы
    skills_str = request.POST.get('skills_list', '')
    if skills_str:
        story.append(Paragraph("SKILLS", s_sb_h))
        for item in skills_str.split(','):
            parts = item.split('-')
            name = parts[0].strip()
            try: lvl = float(parts[1])
            except: lvl = 50
            story.append(ProSkillBar(name, lvl, width=65*mm))
            story.append(Spacer(1, 10))

    # Языки
    langs = request.POST.get('languages')
    if langs:
        story.append(Paragraph("LANGUAGES", s_sb_h))
        story.append(Paragraph(langs, s_sb_t))

    story.append(FrameBreak())

    # --- 2. MAIN CONTENT ---
    story.append(Paragraph(request.POST.get('full_name', 'Your Name'), s_name))
    story.append(Paragraph(request.POST.get('target_role', 'Professional'), s_role))
    
    line = Drawing(400, 2)
    line.add(Line(0, 0, 130*mm, 0, strokeColor=colors.HexColor("#ecf0f1"), strokeWidth=2))
    story.append(line)
    
    # Summary
    about = request.POST.get('about_me')
    if about:
        story.append(Paragraph("PROFILE", s_h2))
        story.append(Paragraph(about, s_body))

    # Experience
    exp = request.POST.get('experience_text')
    if not exp: exp = request.POST.get('resume', '') # Fallback
    
    if exp:
        story.append(Paragraph("WORK EXPERIENCE", s_h2))
        for line in exp.split('\n'):
            line = line.strip()
            if line:
                # Если строка похожа на заголовок (короткая + есть цифры года)
                if len(line) < 80 and any(c.isdigit() for c in line):
                     story.append(Paragraph(f"<b>{line}</b>", s_body))
                else:
                     story.append(Paragraph(line, s_body))

    # References
    refs = request.POST.get('references')
    if refs:
        story.append(Paragraph("REFERENCES", s_h2))
        story.append(Paragraph(refs, s_body))

    doc.build(story)
    buffer.seek(0)
    return FileResponse(buffer, as_attachment=True, filename='CV_Elite.pdf')