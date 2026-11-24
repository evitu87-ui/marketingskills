# Клон голоса Виталия в ElevenLabs: как записать

_24.11.2026. Нужны два голоса: русский и английский. Клонируем только голос Виталия._

## Что понадобится

- Платный тариф ElevenLabs. На бесплатном клонирование голоса и генерация видео (липсинк) недоступны: 24.11 сервис ответил «Video generation needs a paid plan».
- Телефон и тихая комната. Студия не нужна.

## Запись

1. iPhone, приложение «Диктофон». Положите телефон на стол в 15–20 см от лица, не держите в руке.
2. Комната с мягкой мебелью или шторами, окна закрыты, кондиционер и холодильник не гудят рядом.
3. Говорите так, как будете говорить в рилсах: спокойно, уверенно, с паузами. Не читайте монотонно.
4. Каждая запись 2–3 минуты. Оговорились — повторите фразу и идите дальше, вырезать не нужно.
5. Без музыки, без второго голоса, без эха.

## Русский голос

Подходит уже готовая запись для Palm Springs (2:42, Google Drive, папка «Voice msgs»). Если хотите чище, запишите заново текст из `palm-springs-ru/voice-script.md`.

## Английский голос

Прочитайте текст ниже своим обычным английским, с тем акцентом, который есть: клон повторит именно его, и это звучит честнее, чем чужой идеальный акцент.

> Hello, my name is Vitaly. I help people buy property directly from developers in the United Arab Emirates, Oman, Saudi Arabia and Qatar.
>
> Most of my clients ask the same three questions. Is it too late to enter the market? Is the price per square foot fair? And will the developer actually finish the building?
>
> I never answer with a promise. I answer with numbers. First, I look at the price per square foot and compare it with the buildings next door. Second, I check what the developer has already delivered, and whether it was on time. Third, I read the contract before the deposit, not after.
>
> Sometimes the honest answer is: this project is not for you. That is fine. A good decision is one you still agree with five years later.
>
> Property in the Emirates is about protecting and growing capital. It is not about quick flips, and nobody can guarantee growth. What I can do is show you the facts, walk you through the deal from the first payment to the keys, and tell you what I would do in your place.
>
> One, two, three, ten, fifty, one hundred, one thousand, one point eight million dirhams, forty-six percent, two thousand and fifty per square foot.
>
> If you want the details, write to me. The decision is always yours.

## Загрузка в ElevenLabs

Названия кнопок могут немного отличаться.

1. elevenlabs.io → раздел Voices → Add a new voice (или Create or clone a voice).
2. Instant Voice Clone.
3. Загрузите файл записи. Имя голоса: `Vitaly RU` для русского, `Vitaly EN` для английского. Язык в метках укажите соответствующий.
4. Поставьте галочку, что это ваш голос и у вас есть право его клонировать.
5. Сохраните. Сделайте то же для второго языка.

Потом напишите в чат названия голосов. Ключ ElevenLabs в чат не присылайте: для завода он добавляется в n8n как Credentials.

## Голоса ведущих

Виртуальным ведущим клоны не нужны: для них подбираем готовые голоса из библиотеки ElevenLabs, по одному на язык.
