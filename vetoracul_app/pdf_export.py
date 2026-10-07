"""
Генерация PDF-карточки питомца через fpdf2.
Чистый Python — работает одинаково на Windows и Linux, без системных библиотек.
"""
import logging
from pathlib import Path

from django.conf import settings
from fpdf import FPDF
from fpdf.enums import XPos, YPos

logger = logging.getLogger(__name__)


class PetCardPDF(FPDF):
    """Карточка питомца в PDF: титул, данные, диагнозы, напоминания, документы."""

    # ---- Палитра (RGB) ----
    C_PRIMARY       = (107, 70, 193)     # #6b46c1 — акцент
    C_TEXT          = (45, 27, 78)       # #2d1b4e — основной текст
    C_MUTED         = (138, 127, 168)    # #8a7fa8 — приглушённый
    C_BORDER        = (224, 214, 240)    # #e0d6f0 — границы
    C_SOFT_BG       = (245, 240, 255)    # #f5f0ff — мягкий фон
    C_NOTE_BG       = (253, 247, 227)    # #fdf7e3 — заметки
    C_NOTE_BORDER   = (212, 160, 23)     # #d4a017
    C_STATUS_BG     = (237, 233, 254)    # #ede9fe — плашка статуса
    C_STATUS_TX     = (91, 33, 182)      # #5b21b6

    def __init__(self, pet, diagnoses, documents, reminders, co_owners,
                 generated_at, generated_by):
        super().__init__(orientation='P', unit='mm', format='A4')
        self.pet = pet
        self.diagnoses = diagnoses
        self.documents = documents
        self.reminders = reminders
        self.co_owners = co_owners
        self.generated_at = generated_at
        self.generated_by = generated_by

        self.set_margins(14, 14, 14)
        self.set_auto_page_break(auto=True, margin=20)
        self.alias_nb_pages()
        self._register_fonts()

    # ------------------------------------------------------------------
    # Шрифты
    # ------------------------------------------------------------------

    def _resolve_fonts_dir(self):
        """Ищет папку fonts/ в разных возможных местах в зависимости от окружения."""
        candidates = []

        # 1. STATICFILES_DIRS — dev-режим
        static_dirs = getattr(settings, 'STATICFILES_DIRS', None) or []
        for d in static_dirs:
            candidates.append(Path(d) / 'fonts')

        # 2. STATIC_ROOT — production (после collectstatic)
        static_root = getattr(settings, 'STATIC_ROOT', None)
        if static_root:
            candidates.append(Path(static_root) / 'fonts')

        # 3. Папка static приложения — крайний случай
        candidates.append(Path(__file__).resolve().parent / 'static' / 'fonts')

        for path in candidates:
            if path.is_dir():
                return path

        raise FileNotFoundError(
            'Папка fonts/ не найдена. Проверьте STATICFILES_DIRS/STATIC_ROOT '
            'и наличие собранной статики (collectstatic).'
        )

    def _register_fonts(self):
        fonts_dir = self._resolve_fonts_dir()
        regular = fonts_dir / 'PTSans-Regular.ttf'
        bold = fonts_dir / 'PTSans-Bold.ttf'
        italic = fonts_dir / 'PTSans-Italic.ttf'
        bold_italic = fonts_dir / 'PTSans-BoldItalic.ttf'

        if not regular.exists() or not bold.exists():
            raise FileNotFoundError(
                f'Шрифты PT Sans не найдены в {fonts_dir}. '
                'Нужны минимум PTSans-Regular.ttf и PTSans-Bold.ttf.'
            )

        self.add_font('PTSans', '', str(regular))
        self.add_font('PTSans', 'B', str(bold))
        if italic.exists():
            self.add_font('PTSans', 'I', str(italic))
        if bold_italic.exists():
            self.add_font('PTSans', 'BI', str(bold_italic))

    # ------------------------------------------------------------------
    # Утилиты
    # ------------------------------------------------------------------
    @property
    def content_width(self):
        return self.w - self.l_margin - self.r_margin

    def _set_text(self, style='', size=10, color=None):
        self.set_font('PTSans', style, size)
        self.set_text_color(*(color or self.C_TEXT))

    def _safe_break(self, needed_h):
        if self.get_y() + needed_h > self.h - self.b_margin:
            self.add_page()

    def _clip(self, text, w):
        """Обрезает строку, чтобы уложить в ширину w (мм), с «…»."""
        if text is None:
            return ''
        text = str(text)
        if self.get_string_width(text) <= w:
            return text
        while len(text) > 1 and self.get_string_width(text + '…') > w:
            text = text[:-1]
        return text + '…'

    # ------------------------------------------------------------------
    # Шапка
    # ------------------------------------------------------------------
    def _draw_header(self):
        y0 = self.get_y()

        self._set_text('B', 20, self.C_PRIMARY)
        self.cell(100, 9, 'ВетОракул', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self._set_text('', 10, self.C_MUTED)
        self.cell(100, 5, 'Карточка питомца — полная выгрузка',
                  new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        meta_lines = [
            f'Сформировано: {self.generated_at.strftime("%d.%m.%Y %H:%M")}',
            f'Администратор: {self.generated_by.get_full_name() or self.generated_by.username}',
            f'ID питомца: {self.pet.pk}',
        ]
        self._set_text('', 9, self.C_MUTED)
        for i, line in enumerate(meta_lines):
            self.set_xy(self.l_margin, y0 + i * 4.5)
            self.cell(self.content_width, 4.5, line, align='R',
                      new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        self.set_y(y0 + 3 * 4.5 + 2)
        self.set_draw_color(*self.C_PRIMARY)
        self.set_line_width(0.6)
        y = self.get_y()
        self.line(self.l_margin, y, self.w - self.r_margin, y)
        self.ln(4)

    # ------------------------------------------------------------------
    # Имя питомца
    # ------------------------------------------------------------------
    def _draw_pet_name(self):
        self._set_text('B', 22, self.C_TEXT)
        self.cell(0, 12, self.pet.name, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(2)

    # ------------------------------------------------------------------
    # KV-таблица (label / value / label / value)
    # ------------------------------------------------------------------
    def _draw_kv_row(self, cells, widths=(30, 61, 30, 61), line_h=8):
        self._safe_break(line_h)
        y = self.get_y()
        x = self.l_margin

        self.set_draw_color(*self.C_BORDER)
        self.set_line_width(0.2)

        for (text, is_label), w in zip(cells, widths):
            if is_label:
                self.set_fill_color(*self.C_SOFT_BG)
                self.rect(x, y, w, line_h, style='DF')
                self.set_xy(x + 2, y + 2)
                self._set_text('B', 9, self.C_PRIMARY)
                self.cell(w - 4, line_h - 4, self._clip(text, w - 4))
            else:
                self.rect(x, y, w, line_h, style='D')
                self.set_xy(x + 2, y + 2)
                self._set_text('', 9, self.C_TEXT)
                self.cell(w - 4, line_h - 4, self._clip(text, w - 4))
            x += w

        self.set_xy(self.l_margin, y + line_h)

    def _draw_basic_info(self):
        pet = self.pet
        gender = 'Мальчик' if pet.gender == 'M' else 'Девочка'

        if pet.birth_date:
            bd = pet.birth_date.strftime('%d.%m.%Y')
            if pet.age:
                bd += f' ({pet.age} лет)'
        else:
            bd = '—'

        weight = str(pet.weight).rstrip('0').rstrip('.') + ' кг'

        self._draw_kv_row([
            ('Вид', True), (pet.animal_type or '—', False),
            ('Порода', True), (pet.breed or '—', False),
        ])
        self._draw_kv_row([
            ('Пол', True), (gender, False),
            ('Дата рождения', True), (bd, False),
        ])
        self._draw_kv_row([
            ('Вес', True), (weight, False),
            ('Состояние', True), (pet.get_health_status_display(), False),
        ])
        self._draw_kv_row([
            ('Создано', True), (pet.created_at.strftime('%d.%m.%Y %H:%M'), False),
            ('Обновлено', True), (pet.updated_at.strftime('%d.%m.%Y %H:%M'), False),
        ])

    # ------------------------------------------------------------------
    # Заметки
    # ------------------------------------------------------------------
    def _draw_notes(self):
        if not self.pet.notes:
            return
        self.ln(3)

        text_w = self.content_width - 10
        self.set_font('PTSans', '', 9)
        h_text = self.multi_cell(text_w, 5, self.pet.notes, dry_run=True, output='HEIGHT')
        h_total = h_text + 12

        self._safe_break(h_total)
        y0 = self.get_y()

        self.set_fill_color(*self.C_NOTE_BG)
        self.rect(self.l_margin, y0, self.content_width, h_total, style='F')
        self.set_fill_color(*self.C_NOTE_BORDER)
        self.rect(self.l_margin, y0, 1.5, h_total, style='F')

        self.set_xy(self.l_margin + 5, y0 + 2)
        self._set_text('B', 9, (160, 106, 0))
        self.cell(0, 5, 'Особые заметки', new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        self.set_xy(self.l_margin + 5, y0 + 7)
        self._set_text('', 9, self.C_TEXT)
        self.multi_cell(text_w, 5, self.pet.notes)

        self.set_y(y0 + h_total + 2)

    # ------------------------------------------------------------------
    # Статистика
    # ------------------------------------------------------------------
    def _draw_stats(self):
        self.ln(3)
        self._safe_break(22)

        stats = [
            (str(len(self.diagnoses)), 'диагнозов'),
            (str(len(self.reminders)), 'напоминаний'),
            (str(len(self.documents)), 'документов'),
            (str(len(self.co_owners)), 'совладельцев'),
        ]
        cell_w = self.content_width / 4
        y0 = self.get_y()

        self.set_draw_color(*self.C_BORDER)
        self.set_line_width(0.2)

        for i, (num, label) in enumerate(stats):
            x = self.l_margin + i * cell_w
            self.set_fill_color(*self.C_SOFT_BG)
            self.rect(x, y0, cell_w, 18, style='DF')

            self.set_xy(x, y0 + 2)
            self._set_text('B', 16, self.C_PRIMARY)
            self.cell(cell_w, 7, num, align='C', new_x=XPos.LMARGIN, new_y=YPos.NEXT)

            self.set_xy(x, y0 + 11)
            self._set_text('', 8, self.C_MUTED)
            self.cell(cell_w, 5, label, align='C')

        self.set_xy(self.l_margin, y0 + 18 + 4)

    # ------------------------------------------------------------------
    # Секция
    # ------------------------------------------------------------------
    def _section_title(self, text):
        self.ln(3)
        self._safe_break(12)
        self._set_text('B', 12, self.C_PRIMARY)
        self.cell(0, 7, text, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        y = self.get_y()
        self.set_draw_color(*self.C_BORDER)
        self.set_line_width(0.2)
        self.line(self.l_margin, y, self.w - self.r_margin, y)
        self.ln(2)

    # ------------------------------------------------------------------
    # Владелец и совладельцы
    # ------------------------------------------------------------------
    def _draw_owner(self):
        self._section_title('Владелец')
        owner = self.pet.owner
        self._draw_kv_row([
            ('ФИО', True), (owner.get_full_name() or owner.username, False),
            ('Телефон', True), (owner.phone or '—', False),
        ])
        self._draw_kv_row([
            ('Email', True), (owner.email or '—', False),
            ('Город', True), (owner.city or '—', False),
        ])

    def _draw_co_owners(self):
        if not self.co_owners:
            return
        self.ln(3)
        self._set_text('B', 10, self.C_TEXT)
        self.cell(0, 6, 'Совладельцы', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(1)

        widths = [60, 60, 32, 30]
        self._draw_table_header(['ФИО', 'Email', 'Телефон', 'Уровень'], widths)
        for co in self.co_owners:
            self._draw_table_row([
                co.user.get_full_name() or co.user.username,
                co.user.email or '—',
                co.user.phone or '—',
                co.get_access_level_display(),
            ], widths)

    # ------------------------------------------------------------------
    # Диагнозы
    # ------------------------------------------------------------------
    def _draw_diagnoses(self):
        self._section_title(f'Диагнозы — {len(self.diagnoses)}')

        if not self.diagnoses:
            self._set_text('I', 9, self.C_MUTED)
            self.cell(0, 6, 'Диагнозов нет.', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            return

        for d in self.diagnoses:
            self._draw_diagnosis(d)

    def _draw_diagnosis(self, d):
        inner_w = self.content_width - 8
        text_w = inner_w - 24

        self.set_font('PTSans', '', 9)
        h_diag = self.multi_cell(text_w, 5, d.diagnosis_text or '—',
                                 dry_run=True, output='HEIGHT')

        h_treatment = 0
        if d.treatment:
            self.set_font('PTSans', '', 9)
            h_treatment = self.multi_cell(text_w - 4, 5, d.treatment,
                                          dry_run=True, output='HEIGHT') + 8

        h_meta = 5 if d.vet else 0
        h_total = 10 + h_diag + h_treatment + h_meta + 4

        self._safe_break(h_total + 4)
        y0 = self.get_y()
        x0 = self.l_margin

        self.set_fill_color(*self.C_PRIMARY)
        self.rect(x0, y0, 1.5, h_total, style='F')

        self.set_draw_color(*self.C_BORDER)
        self.set_line_width(0.2)
        self.line(x0 + 1.5, y0, self.w - self.r_margin, y0)

        # Дата + статус
        self.set_xy(x0 + 4, y0 + 2)
        self._set_text('B', 10, self.C_TEXT)
        self.cell(35, 5, d.date.strftime('%d.%m.%Y'))

        status_text = d.get_status_display()
        self.set_font('PTSans', 'B', 8)
        pill_w = self.get_string_width(status_text) + 8
        pill_x = x0 + 4 + 35
        pill_y = y0 + 2
        self.set_fill_color(*self.C_STATUS_BG)
        self.rect(pill_x, pill_y, pill_w, 5, style='F',
                  round_corners=True, corner_radius=2.5)
        self.set_xy(pill_x, pill_y + 0.7)
        self.set_text_color(*self.C_STATUS_TX)
        self.cell(pill_w, 4, status_text, align='C')

        # Диагноз
        self.set_xy(x0 + 4, y0 + 9)
        self._set_text('B', 9, self.C_PRIMARY)
        self.cell(20, 5, 'Диагноз:')
        self.set_xy(x0 + 4 + 20, y0 + 9)
        self._set_text('', 9, self.C_TEXT)
        self.multi_cell(text_w, 5, d.diagnosis_text or '—')

        cur_y = self.get_y()

        # Лечение
        if d.treatment:
            cur_y += 2
            treat_w = inner_w - 4
            self.set_fill_color(*self.C_SOFT_BG)
            self.rect(x0 + 6, cur_y, treat_w, h_treatment, style='F')
            self.set_fill_color(*self.C_PRIMARY)
            self.rect(x0 + 6, cur_y, 1, h_treatment, style='F')

            self.set_xy(x0 + 9, cur_y + 2)
            self._set_text('B', 8, self.C_PRIMARY)
            self.cell(0, 4, 'Лечение:', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            self.set_xy(x0 + 9, cur_y + 6)
            self._set_text('', 9, self.C_TEXT)
            self.multi_cell(treat_w - 6, 5, d.treatment)
            cur_y = self.get_y()

        # Врач
        if d.vet:
            cur_y += 1
            self.set_xy(x0 + 4, cur_y)
            self._set_text('', 8, self.C_MUTED)
            self.cell(0, 5, f'Врач: {d.vet.get_full_name() or d.vet.username}',
                      new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            cur_y = self.get_y()

        self.set_y(cur_y + 4)

    # ------------------------------------------------------------------
    # Напоминания
    # ------------------------------------------------------------------
    def _draw_reminders(self):
        self._section_title(f'Напоминания — {len(self.reminders)}')
        if not self.reminders:
            self._set_text('I', 9, self.C_MUTED)
            self.cell(0, 6, 'Напоминаний нет.', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            return

        widths = [25, 16, 57, 29, 26, 29]
        self._draw_table_header(['Дата', 'Время', 'Заголовок', 'Тип', 'Статус', 'Автор'], widths)

        for r in self.reminders:
            time_str = r.time.strftime('%H:%M') if r.time else '—'
            title = r.title or ''
            if r.description:
                title += f'\n{r.description}'
            author = (r.created_by.get_full_name() or r.created_by.username) if r.created_by else '—'
            self._draw_table_row([
                r.date.strftime('%d.%m.%Y'),
                time_str,
                title,
                r.get_reminder_type_display(),
                r.get_status_display(),
                author,
            ], widths)

    # ------------------------------------------------------------------
    # Документы
    # ------------------------------------------------------------------
    def _draw_documents(self):
        self._section_title(f'Документы — {len(self.documents)}')
        if not self.documents:
            self._set_text('I', 9, self.C_MUTED)
            self.cell(0, 6, 'Документов нет.', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            return

        widths = [25, 73, 33, 51]
        self._draw_table_header(['Дата', 'Название', 'Папка', 'Загрузил'], widths)

        for doc in self.documents:
            title = doc.title or doc.file.name.split('/')[-1]
            if doc.description:
                title += f'\n{doc.description}'
            uploader = (doc.uploaded_by.get_full_name() or doc.uploaded_by.username) if doc.uploaded_by else '—'
            self._draw_table_row([
                doc.date.strftime('%d.%m.%Y'),
                title,
                doc.folder.name if doc.folder else '—',
                uploader,
            ], widths)

    # ------------------------------------------------------------------
    # Универсальные таблицы
    # ------------------------------------------------------------------
    def _draw_table_header(self, headers, widths):
        self._safe_break(7)
        y = self.get_y()
        x = self.l_margin

        self.set_draw_color(*self.C_BORDER)
        self.set_line_width(0.2)

        for h, w in zip(headers, widths):
            self.set_fill_color(*self.C_SOFT_BG)
            self.rect(x, y, w, 7, style='DF')
            self.set_xy(x + 1.5, y + 1.5)
            self._set_text('B', 9, self.C_PRIMARY)
            self.cell(w - 3, 4, self._clip(h, w - 3))
            x += w

        self.set_xy(self.l_margin, y + 7)

    def _draw_table_row(self, values, widths):
        line_h = 5
        max_h = line_h
        self.set_font('PTSans', '', 9)

        for v, w in zip(values, widths):
            h = self.multi_cell(w - 3, line_h, str(v if v is not None else '—'),
                                dry_run=True, output='HEIGHT')
            if h > max_h:
                max_h = h
        row_h = max_h + 3

        self._safe_break(row_h)
        y = self.get_y()
        x = self.l_margin

        self.set_draw_color(*self.C_BORDER)
        self.set_line_width(0.2)

        for v, w in zip(values, widths):
            self.rect(x, y, w, row_h, style='D')
            self.set_xy(x + 1.5, y + 1.5)
            self._set_text('', 9, self.C_TEXT)
            self.multi_cell(w - 3, line_h, str(v if v is not None else '—'))
            x += w

        self.set_xy(self.l_margin, y + row_h)

    # ------------------------------------------------------------------
    # Подвал
    # ------------------------------------------------------------------
    def _draw_footer_block(self):
        self.ln(6)
        self._safe_break(20)
        y = self.get_y()
        self.set_draw_color(*self.C_BORDER)
        self.set_line_width(0.2)
        self.line(self.l_margin, y, self.w - self.r_margin, y)
        self.ln(3)

        self._set_text('', 8, self.C_MUTED)
        self.cell(0, 4, 'ВетОракул · vetoracul.ru · vetoracul@yandex.ru · +7 (985) 122-42-41',
                  align='C', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.cell(0, 4, 'ИП Курындина А.С. · ИНН 772607929584 · ОГРНИП 323774600350046',
                  align='C', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self._set_text('I', 8, self.C_MUTED)
        self.cell(0, 4, 'Документ сформирован автоматически и предназначен для служебного использования.',
                  align='C', new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    # ------------------------------------------------------------------
    # Колонтитул на каждой странице
    # ------------------------------------------------------------------
    def footer(self):
        self.set_y(-12)
        self.set_font('PTSans', '', 8)
        self.set_text_color(*self.C_MUTED)
        self.cell(0, 5, f'Стр. {self.page_no()} из {{nb}} · ВетОракул · vetoracul.ru', align='C')

    # ------------------------------------------------------------------
    # Точка входа
    # ------------------------------------------------------------------
    def build(self):
        self.add_page()
        self._draw_header()
        self._draw_pet_name()
        self._draw_basic_info()
        self._draw_notes()
        self._draw_stats()
        self._draw_owner()
        self._draw_co_owners()
        self._draw_diagnoses()
        self._draw_reminders()
        self._draw_documents()
        self._draw_footer_block()
        return bytes(self.output())