# -*- coding: utf-8 -*-
import telebot
import os
import re
from datetime import datetime
from zoneinfo import ZoneInfo
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_RIGHT, TA_LEFT, TA_CENTER
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor
import arabic_reshaper
from bidi.algorithm import get_display

# التوكن الخاص بك
TOKEN = "8678080057:AAHGkanpLQCA20JhhOJ6kxtRVuCxY9oJc6o"
bot = telebot.TeleBot(TOKEN)

# إعدادات الخط العربي والرموز
FONT_PATH = "arial.ttf"
FONT_NAME = "ArabicFont"

if os.path.exists(FONT_PATH):
    pdfmetrics.registerFont(TTFont(FONT_NAME, FONT_PATH))
else:
    FONT_NAME = "Helvetica"

# قاموس ثيمات الألوان
THEMES = {
    "classic": {"primary": "#2C3E50", "secondary": "#BDC3C7", "bg": "#FFFFFF", "name": "🏛️ الملكي الكلاسيكي"},
    "warm": {"primary": "#5D4037", "secondary": "#D7CCC8", "bg": "#FFFDE7", "name": "☕ الدافئ المريح"},
    "modern": {"primary": "#006064", "secondary": "#B2EBF2", "bg": "#FAFAFA", "name": "📱 الحديث المعاصر"}
}

# تخزين إعدادات وجلسات المستخدمين
user_data = {}

def process_arabic_text(text):
    """معالجة النصوص العربية لتبدو متصلة ومن اليمين إلى اليسار"""
    reshaped_text = arabic_reshaper.reshape(text)
    bidi_text = get_display(reshaped_text)
    return bidi_text

def is_line_arabic(text):
    """معرفة إذا كان السطر يحتاج إلى محاذاة لليمين"""
    clean_text = re.sub(r'<[^>]*>', '', text)
    arabic_chars = sum(1 for char in clean_text if '\u0600' <= char <= '\u06FF')
    english_chars = sum(1 for char in clean_text if ('a' <= char.lower() <= 'z'))
    if arabic_chars > 0 or arabic_chars >= english_chars:
        return True
    return False

def convert_markdown_to_html(text):
    """تحويل Markdown الأساسي إلى HTML تدعمه ReportLab"""
    text = re.sub(r'\*\*(.*?)\*\*|__(.__?)__', r'<b>\1\2</b>', text)
    text = re.sub(r'\*(.*?)\*|_(._?)_', r'<i>\1\2</i>', text)
    text = re.sub(r'`(.*?)`', r'<font name="Courier" color="red">\1</font>', text)
    return text

def init_user_settings(chat_id, first_name=""):
    """تهيئة إعدادات المستخدم الافتراضية إذا لم تكن موجودة"""
    if chat_id not in user_data:
        user_data[chat_id] = {
            'text_list': [],
            'font_size': 14,
            'theme': 'classic',
            'watermark': '', # إذا فارغة ستصبح باسمه تلقائياً
            'password': '',
            'user_display_name': first_name if first_name else "مستخدم البوت"
        }

def get_main_settings_keyboard():
    """توليد لوحة التحكم الرئيسية بالأزرار"""
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        telebot.types.InlineKeyboardButton("🎨 اختيار ثيم الألوان", callback_data="menu_theme"),
        telebot.types.InlineKeyboardButton("📏 حجم خط المتن", callback_data="menu_size"),
        telebot.types.InlineKeyboardButton("🏷️ تخصيص علامة مائية", callback_data="menu_watermark"),
        telebot.types.InlineKeyboardButton("🔒 قفل بكلمة سر", callback_data="menu_password")
    )
    return markup

@bot.message_handler(commands=['start', 'help', 'settings'])
def send_welcome(message):
    chat_id = message.chat.id
    init_user_settings(chat_id, message.from_user.first_name)
    
    welcome_text = (
        "👑 **مرحباً بك في منصة توليد الـ PDF الاحترافية الشاملة!**\n\n"
        "⚙️ **لوحة التحكم والأزرار:**\n"
        "يمكنك تخصيص كل ميزات المستند الخاص بك مباشرة من الأزرار أدناه بدون الحاجة لكتابة أوامر يدوية.\n\n"
        "📥 **بدء العمل:**\n"
        "أرسل أول نص أو ملف نصي مباشرة وسأقوم بتجميعه وتنسيقه لك."
    )
    bot.send_message(chat_id, welcome_text, parse_mode="Markdown", reply_markup=get_main_settings_keyboard())

@bot.callback_query_handler(func=lambda call: call.data.startswith("menu_"))
def handle_menu_navigation(call):
    chat_id = call.message.chat.id
    init_user_settings(chat_id, call.from_user.first_name)
    action = call.data.split("_")[1]
    bot.answer_callback_query(call.id)
    
    if action == "theme":
        markup = telebot.types.InlineKeyboardMarkup()
        for key, value in THEMES.items():
            markup.add(telebot.types.InlineKeyboardButton(value['name'], callback_data=f"settheme_{key}"))
        markup.add(telebot.types.InlineKeyboardButton("⬅️ العودة للرئيسية", callback_data="back_main"))
        bot.edit_message_text("🎨 اختر ثيم الألوان المفضل لصفحات مستندك:", chat_id, call.message.message_id, reply_markup=markup)
        
    elif action == "size":
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(
            telebot.types.InlineKeyboardButton("صغير (12)", callback_data="setsize_12"),
            telebot.types.InlineKeyboardButton("متوسط (14)", callback_data="setsize_14"),
            telebot.types.InlineKeyboardButton("كبير (18)", callback_data="setsize_18")
        )
        markup.add(telebot.types.InlineKeyboardButton("⬅️ العودة للرئيسية", callback_data="back_main"))
        bot.edit_message_text("📏 اختر حجم خط المتن المناسب للتقرير:", chat_id, call.message.message_id, reply_markup=markup)
        
    elif action == "watermark":
        msg = bot.send_message(chat_id, "📝 أرسل العبارة التي تريدها كعلامة مائية مخصصة (أو أرسل 'تلقائي' لنجعلها باسم حسابك):")
        bot.register_next_step_handler(msg, save_watermark)
        
    elif action == "password":
        msg = bot.send_message(chat_id, "🔑 أرسل كلمة السر التي تود قفل وحماية المستند بها (أو أرسل 'الغاء' لإزالة القفل):")
        bot.register_next_step_handler(msg, save_password)

@bot.callback_query_handler(func=lambda call: call.data == "back_main")
def handle_back_main(call):
    chat_id = call.message.chat.id
    bot.answer_callback_query(call.id)
    bot.edit_message_text("⚙️ يمكنك التحكم وتخصيص كل ميزات المستند من هنا عبر الأزرار لراحة تامة:", chat_id, call.message.message_id, reply_markup=get_main_settings_keyboard())

@bot.callback_query_handler(func=lambda call: call.data.startswith("settheme_"))
def handle_set_theme(call):
    chat_id = call.message.chat.id
    theme_key = call.data.split("_")[1]
    user_data[chat_id]['theme'] = theme_key
    bot.answer_callback_query(call.id, f"تم تفعيل ثيم {THEMES[theme_key]['name']}")
    bot.edit_message_text(f"✅ تم حفظ الإعدادات! الثيم الفعال حالياً هو: **{THEMES[theme_key]['name']}**", chat_id, call.message.message_id, reply_markup=get_main_settings_keyboard(), parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("setsize_"))
def handle_set_size(call):
    chat_id = call.message.chat.id
    size = int(call.data.split("_")[1])
    user_data[chat_id]['font_size'] = size
    bot.answer_callback_query(call.id, f"تم تغيير حجم الخط إلى {size}")
    bot.edit_message_text(f"✅ تم حفظ الإعدادات! حجم خط المتن الحالي هو: **{size}**", chat_id, call.message.message_id, reply_markup=get_main_settings_keyboard(), parse_mode="Markdown")

def save_watermark(message):
    chat_id = message.chat.id
    init_user_settings(chat_id, message.from_user.first_name)
    text = message.text.strip()
    if text == "تلقائي" or text == "الغاء":
        user_data[chat_id]['watermark'] = ""
        bot.reply_to(message, "✅ تم تعيين العلامة المائية لتكون تلقائية باسمك في تليجرام.")
    else:
        user_data[chat_id]['watermark'] = text
        bot.reply_to(message, f"✅ تم حفظ العلامة المائية المخصصة بنجاح: `{text}`", parse_mode="Markdown")
    bot.send_message(chat_id, "⚙️ لوحة التحكم:", reply_markup=get_main_settings_keyboard())

def save_password(message):
    chat_id = message.chat.id
    init_user_settings(chat_id, message.from_user.first_name)
    text = message.text.strip()
    if text == "الغاء" or text == "إلغاء":
        user_data[chat_id]['password'] = ""
        bot.reply_to(message, "🔓 تم إلغاء قفل الملفات.")
    else:
        user_data[chat_id]['password'] = text
        bot.reply_to(message, "🔒 تم تفعيل حماية وتشفير المستندات بكلمة السر الخاصة بك!")
    bot.send_message(chat_id, "⚙️ لوحة التحكم:", reply_markup=get_main_settings_keyboard())

@bot.message_handler(content_types=['document'])
def handle_incoming_document(message):
    chat_id = message.chat.id
    init_user_settings(chat_id, message.from_user.first_name)
    file_name = message.document.file_name
    
    if file_name.endswith(('.txt', '.py', '.java', '.cpp', '.html', '.css', '.json', '.js')):
        status = bot.reply_to(message, "⏳ جاري قراءة محتويات الملف النصي المرفوع...")
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        try:
            file_content = downloaded_file.decode('utf-8')
        except UnicodeDecodeError:
            try:
                file_content = downloaded_file.decode('windows-1256')
            except Exception:
                bot.edit_message_text("❌ عذراً، لم نتمكن من قراءة ترميز الملف النصي.", chat_id, status.message_id)
                return
        bot.delete_message(chat_id, status.message_id)
        message.text = file_content
        handle_incoming_text(message)
    else:
        bot.reply_to(message, "⚠️ يرجى إرسال ملفات نصية كودية أو عادية فقط (مثل .txt, .py).")

@bot.message_handler(content_types=['text'])
def handle_incoming_text(message):
    chat_id = message.chat.id
    init_user_settings(chat_id, message.from_user.first_name)
    
    formatted_text = convert_markdown_to_html(message.text)
    user_data[chat_id]['text_list'].append(formatted_text)
    
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(
        telebot.types.InlineKeyboardButton("➕ إضافة نص آخر", callback_data="action_add"),
        telebot.types.InlineKeyboardButton("✅ هاهية (توليد المستند)", callback_data="action_finish")
    )
    bot.reply_to(message, "📥 تم دمج وحفظ النص الحالي. ماذا تريد أن تفعل الآن؟", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("action_"))
def handle_pdf_actions(call):
    chat_id = call.message.chat.id
    if call.data == "action_add":
        bot.edit_message_text("📥 تفضل أرسل النص التالي أو ملفاً نصياً مباشرة، وسأقوم بدمجه وترتيبه بالتسلسل:", chat_id, call.message.message_id)
    elif call.data == "action_finish":
        if chat_id not in user_data or not user_data[chat_id]['text_list']:
            bot.answer_callback_query(call.id, "⚠️ قائمة النصوص فارغة!")
            return
        bot.answer_callback_query(call.id)
        msg = bot.send_message(chat_id, "📝 ممتاز! أرسل الآن الاسم المخصص الذي تريده لملف الـ PDF:")
        bot.register_next_step_handler(msg, handle_file_name_v5)

def handle_file_name_v5(message):
    chat_id = message.chat.id
    if not message.text:
        msg = bot.reply_to(message, "❌ يرجى إرسال اسم نصي صالح:")
        bot.register_next_step_handler(msg, handle_file_name_v5)
        return

    file_name = message.text.strip().replace("/", "_").replace("\\", "_")
    if chat_id not in user_data:
        bot.send_message(chat_id, "⚠️ حدث خطأ فني، يرجى إعادة المحاولة.")
        return
        
    user_data[chat_id]['file_name'] = file_name
    generate_pdf_v5(chat_id)

def generate_pdf_v5(chat_id):
    data = user_data[chat_id]
    text_list = data['text_list']
    file_name = data['file_name']
    font_size = data['font_size']
    theme_key = data.get('theme', 'classic')
    watermark_text = data.get('watermark', '')
    password = data.get('password', '')
    user_display_name = data.get('user_display_name', 'مستخدم البوت')
    
    # إذا لم يخصص المستخدم علامة مائية، تصبح تلقائياً باسم حسابه لتختلف بين الجميع
    if not watermark_text:
        watermark_text = f"حقوق: {user_display_name}"
        
    theme_colors = THEMES.get(theme_key, THEMES['classic'])
    status_msg = bot.send_message(chat_id, "⏳ جاري تنسيق السطور وبناء الإطارات وحساب حجم الملف الفعلي...")
    pdf_filename = f"{file_name}_{chat_id}.pdf"
    
    try:
        combined_raw_text = "\n".join(text_list)
        clean_for_stats = re.sub(r'<[^>]*>', '', combined_raw_text)
        word_count = len(clean_for_stats.split())
        line_count = len(clean_for_stats.split('\n'))
        baghdad_tz = ZoneInfo("Asia/Baghdad")
        current_date = datetime.now(baghdad_tz).strftime("%Y-%m-%d %I:%M %p")
        
        doc = SimpleDocTemplate(
            pdf_filename, 
            pagesize=A4,
            rightMargin=56, leftMargin=56, topMargin=56, bottomMargin=56
        )
        
        styles = getSampleStyleSheet()
        story = []
        
        lines = combined_raw_text.split('\n')
        for idx, line in enumerate(lines):
            if line.strip():
                # 1. ميزة العناوين الرئيسية المحددة بـ <نص>
                if line.strip().startswith("&lt;") and line.strip().endswith("&gt;"):
                    # استخراج العنوان وحذف التاجات
                    title_content = line.strip().replace("&lt;", "").replace("&gt;", "")
                    if is_line_arabic(title_content):
                        processed_line = process_arabic_text(title_content)
                    else:
                        processed_line = title_content
                    
                    # نمط فخم ومميز للعنوان الرئيسي (أكبر حجماً ومحاذاة بالوسط وبلون الثيم)
                    line_style = ParagraphStyle(
                        f'TitleStyle_{idx}',
                        parent=styles['Heading1'],
                        fontName=FONT_NAME,
                        fontSize=font_size + 5,
                        textColor=HexColor(theme_colors['primary']),
                        leading=font_size + 12,
                        alignment=TA_CENTER,
                        spaceAfter=12,
                        spaceBefore=12
                    )
                    story.append(Paragraph(f"<b>{processed_line}</b>", line_style))
                
                # 2. السطور العادية (متن)
                else:
                    if is_line_arabic(line):
                        alignment = TA_RIGHT
                        processed_line = process_arabic_text(line)
                    else:
                        alignment = TA_LEFT
                        processed_line = line
                    
                    line_style = ParagraphStyle(
                        f'LineStyle_{idx}',
                        parent=styles['Normal'],
                        fontName=FONT_NAME,
                        fontSize=font_size,
                        leading=font_size + 6,
                        alignment=alignment
                    )
                    story.append(Paragraph(processed_line, line_style))
            else:
                story.append(Spacer(1, 10))
                
        # دالة الإطار الجمالي، الخلفية وتخصيص العلامة المائية الفريدة لكل مستخدم
        def draw_page_decorations(canvas, doc):
            canvas.saveState()
            width, height = A4
            
            # تلوين خلفية الصفحة حسب الثيم الفعال
            canvas.setFillColor(HexColor(theme_colors['bg']))
            canvas.rect(0, 0, width, height, fill=True, stroke=False)
            
            # رسم إطارات مزدوجة ملونة ومتناسقة
            canvas.setStrokeColor(HexColor(theme_colors['primary']))
            canvas.setLineWidth(1.5)
            padding = 30
            canvas.rect(padding, padding, width - (padding * 2), height - (padding * 2))
            
            canvas.setStrokeColor(HexColor(theme_colors['secondary']))
            canvas.setLineWidth(0.5)
            canvas.rect(padding + 4, padding + 4, width - ((padding + 4) * 2), height - ((padding + 4) * 2))
            
            # رسم العلامة المائية المخصصة/التلقائية بالخلفية
            canvas.setFont(FONT_NAME, 40)
            canvas.setFillColor(HexColor(theme_colors['primary']))
            canvas.setFillAlpha(0.12)
            canvas.saveState()
            canvas.translate(width/2, height/2)
            canvas.rotate(45)
            canvas.drawCentredString(0, 0, process_arabic_text(watermark_text))
            canvas.restoreState()
            canvas.setFillAlpha(1.0)
            
            # طباعة التذييل ورقم الصفحة وحفظ حقوق البوت
            canvas.setFont(FONT_NAME, 9)
            canvas.setFillColor(HexColor(theme_colors['primary']))
            footer_processed = process_arabic_text(f"صفحة {doc.page}")
            canvas.drawRightString(width - 56, 42, footer_processed)
            
            canvas.restoreState()

        # قفل الملف وحمايته بكلمة سر قبل البناء إن وجدت
        if password:
            from reportlab.lib.pdfencrypt import StandardEncryption
            doc.encrypt = StandardEncryption(password, canPrint=1, canModify=0, canCopy=1)
            
        doc.build(story, onFirstPage=draw_page_decorations, onLaterPages=draw_page_decorations)
        
        # حساب حجم الملف الفعلي بالكيلوبايت (KB)
        file_size_kb = round(os.path.getsize(pdf_filename) / 1024, 2)
        
        # إنشاء ملخص المستند الاحترافي بالكامل داخل وصف الرسالة (Caption) في تليجرام
        caption_summary = (
            f"✅ **تم توليد المستند بنجاح واحترافية عالية!**\n\n"
            f"📊 **ملخص المستند الفني:**\n"
            f"📄 اسم الملف: `{file_name}.pdf`\n"
            f"📦 حجم الملف: `{file_size_kb} KB`\n"
            f"📝 إجمالي الكلمات: `{word_count}` كلمة\n"
            f"🔢 إجمالي الأسطر: `{line_count}` سطر\n"
            f"🏷️ العلامة المائية للـ PDF: `{watermark_text}`\n"
            f"🔒 الحماية بكلمة سر: {'🔒 مفعلة ومقفل' if password else '🔓 غير مقفل (عام)'}\n"
            f"📆 تاريخ الإنشاء: `{current_date}`"
        )
        
        # إرسال الملف المسمى للمصمم بوصف تفصيلي شامل
        with open(pdf_filename, 'rb') as pdf_file:
            bot.send_document(
                chat_id, pdf_file, 
                visible_file_name=f"{file_name}.pdf", 
                caption=caption_summary, parse_mode="Markdown"
            )
            
        bot.delete_message(chat_id, status_msg.message_id)
        
        # تنظيف السيرفر وحذف المؤقتات لحماية الخصوصية
        if os.path.exists(pdf_filename):
            os.remove(pdf_filename)
        user_data.pop(chat_id, None)
        
    except Exception as e:
        bot.edit_message_text(f"❌ حدث خطأ فني أثناء معالجة المستند: {str(e)}", chat_id, status_msg.message_id)
        if os.path.exists(pdf_filename):
            os.remove(pdf_filename)

if __name__ == '__main__':
    print("🤖 البوت النهائي المتكامل يعمل الآن بنجاح وبكافة الأزرار التفاعلية...")
    bot.infinity_polling()