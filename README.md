# 🎙️ HASHKA VLOG EDIT

Подкастаа (улс төр, нийгэм, сэтгэл зүй) бүтнээр нь засаж, хэсгээс нь тогтмол reel хийх **Claude Code**-оор мэргэжлийн түвшинд хийх систем:
**ffmpeg** (тайралт, дуу) + **faster-whisper** (монгол яриа → текст) + **Remotion** (анимацитай монгол субтитр, hook гарчиг).

## Юу хийж чадах вэ
- 🔊 **Дуу цэвэрлэх**: чимээ дарах, компрессор, loudness (Reels −14 / YouTube −16 LUFS)
- ✂️ **Чимээгүй хэсгийг автоматаар хасах** (амьсгалыг үлдээнэ)
- 📝 **Монгол транскрипт**: үг бүрийн цагтай, `.srt` (YouTube-д оруулах)
- 📱 **16:9 → 9:16 reel**: `crop` (нэг хүн), `split` (2 хүн дээр-доор), `blur` (бүтэн кадр + бүдэг фон)
- ✨ **TikTok маягийн субтитр**: ярьж буй үг шараар тодорно, Ө/Ү зөв фонт, hook гарчиг, progress bar, @брэнд
- 🤖 **Claude reel сонгоно**: транскриптээс хамгийн хүчтэй 30–60 сек хэсгийг олж, гарчиг санал болгоно

## Суулгах — Windows 11 (нэг удаа)

> ⚠️ Доорх командуудыг **PowerShell**-д бичнэ. `/reel`, `/podcast` гэх мэт `/`-ээр эхэлсэн командуудыг харин **Claude Code дотор** бичнэ (PowerShell-д биш).

**1. Git суулгах** (PowerShell):
```powershell
winget install -e --id Git.Git
```
PowerShell-ээ хаагаад дахин нээнэ.

**2. Репог татах:**
```powershell
cd $HOME\Documents
```
```powershell
git clone https://github.com/hashkavlog-oss/HASHKA-VLOG-EDIT.git
```
```powershell
cd HASHKA-VLOG-EDIT
```

**3. Бүгдийг суулгах** (ffmpeg, Node.js, Python, сангууд):
```powershell
powershell -ExecutionPolicy Bypass -File .\setup.ps1
```
"PowerShell-ээ хаагаад дахин нээ" гэвэл тэгээд, `cd $HOME\Documents\HASHKA-VLOG-EDIT` хийж, 3-р алхмыг дахин ажиллуулна.

**4. Claude Code эхлүүлэх** (энэ хавтсан дотроо):
```powershell
claude
```
Claude Code суугаагүй бол эхлээд суулгана:
```powershell
irm https://claude.ai/install.ps1 | iex
```
Эсвэл **Claude Desktop app → Code** таб руу ороод энэ хавтсыг (`Documents\HASHKA-VLOG-EDIT`) сонгоно.

<details><summary>Mac дээр бол</summary>

```bash
brew install ffmpeg node python && ./setup.sh
```
</details>

## Claude Code-д хэрхэн хэлэх вэ

Видеогоо `Documents\HASHKA-VLOG-EDIT\input\` хавтсанд хуулаад, Claude Code дотор:

| Бичих | Юу болох |
|---|---|
| `/podcast input/ep12.mp4` | Бүтэн дугаар: дуу цэвэрлэж, чимээгүйг хасаад SRT болон YouTube тайлбар, chapters гаргана |
| `/reel input/ep12.mp4` | (эхлээд `/podcast` хийсэн бол засагдсан хувилбараас нь) 3–5 reel санал болгож, таны сонгосныг render хийнэ |
| `/reel input/ep12.mp4 сэтгэл түгшилтийн тухай` | Тухайн сэдвээр reel хайна |
| `/fix-subs work/ep12` | Монгол субтитрийн алдааг засна |
| "12:30–13:15 хэсгийг reel болго, гарчиг нь 'Стрессээ яаж тайлах вэ?'" | Шууд хийнэ |

## Гараар ажиллуулах (PowerShell)

```powershell
python scripts/edit.py podcast input/ep12.mp4
```
```powershell
python scripts/edit.py reel output/ep12_episode.mp4 --start 12:30 --end 13:15 --title "Стрессээ яаж тайлах вэ?" --layout split --x 0.25 --x2 0.75 --brand @hashka
```
```powershell
python scripts/edit.py -h
```

Бүх команд: `info`, `frame`, `enhance`, `cutsilence`, `transcribe`, `srt2json`, `clip`, `render`, `reel`, `burn`, `podcast`.

## Субтитр зөв гаргах
Whisper монгол хэлэнд 100% биш. Чанарыг сайжруулах 3 арга:
1. `config/whisper_prompt.txt` — подкастын сэдэв, байнга гардаг нэр томьёо. **Зочин бүрийн нэр, нам, байгууллагын нэрийг энд нэмбэл** зөв бичигдэнэ.
2. `config/dictionary.txt` — байнга буруу сонсдог үгс `буруу => зөв`.
3. `/fix-subs` — Claude `captions.srt`-г засаж, `captions.json`-г дахин үүсгэнэ.

GPU байвал Whisper автоматаар GPU ашиглана. CPU дээр `large-v3` модель 1 цагийн аудиог ~1–2 цагт таньдаг. Хурдан хэрэгтэй бол `--model medium`.

## Загвар өөрчлөх
- Өнгө: `--accent "#FF3B6B"`, байрлал: `--captionY 0.6`, ТОМ ҮСЭГ: `--upper`
- Дизайн код: `remotion/src/components/` (Captions, HookTitle, Overlay)
- Урьдчилан харах: `cd remotion; npm run dev`

## Бүтэц
```
input/    ← эх видео (git-д орохгүй)
work/     ← транскрипт, captions, түр файл
output/   ← бэлэн видео
scripts/  ← edit.py (бүх команд), captions.py, common.py
remotion/ ← Remotion төсөл (Reel 1080x1920, Wide 1920x1080)
config/   ← whisper prompt, толь бичиг, Claude тохиргооны жишээ
CLAUDE.md, TOKEN-SAVING.md, .claude/commands/
```

💡 Токен хэмнэх зөвлөгөө: [TOKEN-SAVING.md](TOKEN-SAVING.md)
