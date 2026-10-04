import { workflow, node, trigger, sticky, placeholder, newCredential, ifElse, switchCase, merge, splitInBatches, nextBatch, languageModel, memory, tool, outputParser, embedding, embeddings, vectorStore, retriever, documentLoader, textSplitter, reranker, fromAi, expr } from '@n8n/workflow-sdk';

const briefIn = trigger({
  type: 'n8n-nodes-base.webhook',
  version: 2.1,
  config: {
    name: 'Бриф (webhook video-prod)',
    parameters: { httpMethod: 'POST', path: 'video-prod', responseMode: 'onReceived' },
    position: [0, 300]
  },
  output: [{ body: { project: 'canal-front', image_url: 'https://example.com/photo.jpg', brief: 'Башни Billionaire Row, золотой час, наезд', orientation: '9:16' } }]
});

const normalize = node({
  type: 'n8n-nodes-base.set',
  version: 3.5,
  config: {
    name: 'Нормализовать бриф',
    parameters: {
      mode: 'manual',
      includeOtherFields: false,
      assignments: {
        assignments: [
          { id: 'project', name: 'project', value: expr("{{ $json.body?.project ?? 'test' }}"), type: 'string' },
          { id: 'image_url', name: 'image_url', value: expr("{{ $json.body?.image_url ?? '' }}"), type: 'string' },
          { id: 'brief', name: 'brief', value: expr("{{ $json.body?.brief ?? '' }}"), type: 'string' },
          { id: 'prompt_override', name: 'prompt_override', value: expr("{{ $json.body?.prompt ?? '' }}"), type: 'string' },
          { id: 'orientation', name: 'orientation', value: expr("{{ $json.body?.orientation ?? '9:16' }}"), type: 'string' },
          { id: 'model', name: 'model', value: expr("{{ $json.body?.model ?? 'veo-3.1-fast-generate-preview' }}"), type: 'string' },
          { id: 'duration', name: 'duration', value: expr('{{ Number($json.body?.duration ?? 8) }}'), type: 'number' },
          { id: 'chat_id', name: 'chat_id', value: expr("{{ $json.body?.chat_id ?? '-1004402230561' }}"), type: 'string' },
          { id: 'file_key', name: 'file_key', value: expr("{{ 'video-prod/' + ($json.body?.project ?? 'test') + '/' + $now.toFormat('yyyyLLdd-HHmmss') + '.mp4' }}"), type: 'string' },
          { id: 's3_url', name: 's3_url', value: expr("{{ 'https://s3.twcstorage.ru/menaoffplan-media/video-prod/' + ($json.body?.project ?? 'test') + '/' + $now.toFormat('yyyyLLdd-HHmmss') + '.mp4' }}"), type: 'string' }
        ]
      }
    },
    position: [260, 300]
  },
  output: [{ project: 'canal-front', image_url: 'https://example.com/photo.jpg', brief: 'Башни Billionaire Row', prompt_override: '', orientation: '9:16', model: 'veo-3.1-fast-generate-preview', duration: 8, chat_id: '-1004402230561', file_key: 'video-prod/canal-front/20261004-180000.mp4', s3_url: 'https://s3.twcstorage.ru/menaoffplan-media/video-prod/canal-front/20261004-180000.mp4' }]
});

const downloadPhoto = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.5,
  config: {
    name: 'Скачать фото',
    parameters: {
      method: 'GET',
      url: expr('{{ $json.image_url }}'),
      options: { response: { response: { responseFormat: 'file', outputPropertyName: 'photo' } }, timeout: 60000 }
    },
    position: [520, 300]
  },
  output: [{ photo: 'binary' }]
});

const photoToBase64 = node({
  type: 'n8n-nodes-base.code',
  version: 2,
  config: {
    name: 'Фото → base64',
    parameters: {
      mode: 'runOnceForAllItems',
      language: 'javaScript',
      jsCode: "const item = $input.first();\nconst bin = item.binary && item.binary.photo;\nif (!bin) throw new Error('Фото не скачалось: нет binary.photo');\nconst buf = await this.helpers.getBinaryDataBuffer(0, 'photo');\nreturn [{ json: { image_b64: buf.toString('base64'), mime: bin.mimeType || 'image/jpeg', size: buf.length } }];"
    },
    position: [780, 300]
  },
  output: [{ image_b64: '...', mime: 'image/jpeg', size: 102765 }]
});

const claudePrompt = node({
  type: '@n8n/n8n-nodes-langchain.anthropic',
  version: 1,
  config: {
    name: 'Claude: промпт для Veo',
    parameters: {
      resource: 'text',
      operation: 'message',
      modelId: { __rl: true, mode: 'id', value: 'claude-sonnet-5' },
      messages: {
        values: [
          {
            role: 'user',
            content: expr("БРИФ ОПЕРАТОРА: {{ $('Нормализовать бриф').item.json.brief }}\nОРИЕНТАЦИЯ КАДРА: {{ $('Нормализовать бриф').item.json.orientation }}\nПРОМПТ ОТ ОПЕРАТОРА (если не пустой — возьми его за основу, только доведи до стандарта): {{ $('Нормализовать бриф').item.json.prompt_override }}\n\nВерни ТОЛЬКО JSON без пояснений.")
          }
        ]
      },
      simplify: true,
      options: {
        includeMergedResponse: true,
        maxTokens: 800,
        temperature: 0.6,
        system: "Ты — режиссёр-оператор премиальной недвижимости (Дубай, Billionaire Row, Dubai Water Canal). Тебе дают реальную ФОТОГРАФИЮ объекта и короткий бриф. Задача — написать промпт для модели image-to-video Veo 3.1, который заставит камеру ПЛАВНО двигаться внутри этого кадра, НЕ меняя сам объект.\n\nЖЁСТКИЕ ПРАВИЛА:\n1. Камера только мягкая: slow push-in, gentle dolly, subtle parallax, orbit не более 20°. Никаких резких движений, никаких облётов на 360°.\n2. Запрещено достраивать и менять: no new buildings, no new furniture, no people, no text, no captions, no logos, keep all geometry, materials and layout exactly as in the photo.\n3. Свет: golden hour / warm late-afternoon light, если бриф не говорит иного. Эстетика: cinematic, photorealistic, premium real-estate film.\n4. Промпт на английском, 40–90 слов, одно-два предложения, структура: subject + camera move + light + style + constraints.\n5. negative_prompt — через запятую, на английском.\n\nФормат ответа — строго JSON:\n{\"veo_prompt\": \"...\", \"negative_prompt\": \"...\", \"camera\": \"push-in|dolly|parallax|orbit\", \"notes\": \"одна строка по-русски для оператора\"}"
      }
    },
    credentials: { anthropicApi: { id: 'L3Ed8Fs3JnS42mBW', name: 'Anthropic account' } },
    position: [1040, 300]
  },
  output: [{ merged: '{"veo_prompt":"Slow cinematic push-in...","negative_prompt":"text, people","camera":"push-in","notes":"ок"}' }]
});

const parsePrompt = node({
  type: 'n8n-nodes-base.code',
  version: 2,
  config: {
    name: 'Разобрать JSON промпта',
    parameters: {
      mode: 'runOnceForAllItems',
      language: 'javaScript',
      jsCode: "const j = $input.first().json;\nlet text = '';\nif (typeof j.merged === 'string') text = j.merged;\nelse if (typeof j.text === 'string') text = j.text;\nelse if (Array.isArray(j.content)) text = j.content.map(c => (c && c.text) ? c.text : '').join('');\nelse text = JSON.stringify(j);\nconst m = String(text).match(/\\{[\\s\\S]*\\}/);\nlet out = {};\ntry { out = m ? JSON.parse(m[0]) : {}; } catch (e) { out = {}; }\nconst norm = $('Нормализовать бриф').first().json;\nconst override = (norm.prompt_override || '').trim();\nconst veo_prompt = out.veo_prompt || override || String(text).slice(0, 600);\nconst negative_prompt = out.negative_prompt || 'text, captions, subtitles, watermark, logo, people, faces, distorted architecture, extra buildings, warped geometry, flicker';\nreturn [{ json: { veo_prompt, negative_prompt, camera: out.camera || '', notes: out.notes || '' } }];"
    },
    position: [1300, 300]
  },
  output: [{ veo_prompt: 'Slow cinematic push-in along a waterfront canal lined with modern towers at golden hour...', negative_prompt: 'text, people', camera: 'push-in', notes: 'ок' }]
});

const veoStart = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.5,
  config: {
    name: 'Veo: запуск генерации',
    parameters: {
      method: 'POST',
      url: expr("https://generativelanguage.googleapis.com/v1beta/models/{{ $('Нормализовать бриф').item.json.model }}:predictLongRunning"),
      authentication: 'genericCredentialType',
      genericAuthType: 'httpHeaderAuth',
      sendBody: true,
      contentType: 'json',
      specifyBody: 'json',
      jsonBody: expr("{{ JSON.stringify({ instances: [{ prompt: $json.veo_prompt, image: { bytesBase64Encoded: $('Фото → base64').item.json.image_b64, mimeType: $('Фото → base64').item.json.mime } }], parameters: { aspectRatio: $('Нормализовать бриф').item.json.orientation, negativePrompt: $json.negative_prompt, resolution: '1080p', personGeneration: 'dont_allow', durationSeconds: $('Нормализовать бриф').item.json.duration } }) }}"),
      options: { timeout: 120000 }
    },
    credentials: { httpHeaderAuth: { id: 'a1gKYqEJrOK6sguw', name: 'Gemini API' } },
    position: [1560, 300]
  },
  output: [{ name: 'models/veo-3.1-fast-generate-preview/operations/abc123' }]
});

const saveOp = node({
  type: 'n8n-nodes-base.set',
  version: 3.5,
  config: {
    name: 'Сохранить операцию',
    parameters: {
      mode: 'manual',
      includeOtherFields: false,
      assignments: { assignments: [ { id: 'op', name: 'op_name', value: expr('{{ $json.name }}'), type: 'string' } ] }
    },
    position: [1820, 300]
  },
  output: [{ op_name: 'models/veo-3.1-fast-generate-preview/operations/abc123' }]
});

const waitPoll = node({
  type: 'n8n-nodes-base.wait',
  version: 1.1,
  config: {
    name: 'Подождать 15 с',
    parameters: { resume: 'timeInterval', amount: 15, unit: 'seconds' },
    position: [2080, 300]
  },
  output: [{ op_name: 'models/veo-3.1-fast-generate-preview/operations/abc123' }]
});

const veoStatus = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.5,
  config: {
    name: 'Veo: проверить статус',
    parameters: {
      method: 'GET',
      url: expr("https://generativelanguage.googleapis.com/v1beta/{{ $('Сохранить операцию').item.json.op_name }}"),
      authentication: 'genericCredentialType',
      genericAuthType: 'httpHeaderAuth',
      options: { timeout: 60000 }
    },
    credentials: { httpHeaderAuth: { id: 'a1gKYqEJrOK6sguw', name: 'Gemini API' } },
    position: [2340, 300]
  },
  output: [{ name: 'models/veo-3.1-fast-generate-preview/operations/abc123', done: true, response: { generateVideoResponse: { generatedSamples: [{ video: { uri: 'https://generativelanguage.googleapis.com/v1beta/files/xyz:download?alt=media' } }] } } }]
});

const isDone = ifElse({
  version: 2.3,
  config: {
    name: 'Готово?',
    parameters: {
      conditions: {
        options: { caseSensitive: true, leftValue: '', typeValidation: 'loose', version: 2 },
        conditions: [ { id: 'done', leftValue: expr('{{ $json.done }}'), rightValue: '', operator: { type: 'boolean', operation: 'true', singleValue: true } } ],
        combinator: 'and'
      },
      looseTypeValidation: true
    },
    position: [2600, 300]
  }
});

const extractUri = node({
  type: 'n8n-nodes-base.code',
  version: 2,
  config: {
    name: 'Извлечь ссылку на видео',
    parameters: {
      mode: 'runOnceForAllItems',
      language: 'javaScript',
      jsCode: "const r = $input.first().json;\nconst resp = r.response || {};\nconst gv = resp.generateVideoResponse || resp;\nconst samples = gv.generatedSamples || gv.videos || [];\nconst s0 = samples[0] || {};\nconst uri = (s0.video && s0.video.uri) || s0.uri || '';\nconst reasons = gv.raiMediaFilteredReasons || [];\nconst err = r.error ? (r.error.message || JSON.stringify(r.error)) : '';\nreturn [{ json: { video_uri: uri, filtered: reasons.join('; ') || err, response_keys: Object.keys(resp) } }];"
    },
    position: [2860, 200]
  },
  output: [{ video_uri: 'https://generativelanguage.googleapis.com/v1beta/files/xyz:download?alt=media', filtered: '', response_keys: ['generateVideoResponse'] }]
});

const hasVideo = ifElse({
  version: 2.3,
  config: {
    name: 'Видео есть?',
    parameters: {
      conditions: {
        options: { caseSensitive: true, leftValue: '', typeValidation: 'loose', version: 2 },
        conditions: [ { id: 'uri', leftValue: expr('{{ $json.video_uri }}'), rightValue: '', operator: { type: 'string', operation: 'notEmpty', singleValue: true } } ],
        combinator: 'and'
      },
      looseTypeValidation: true
    },
    position: [3120, 200]
  }
});

const downloadMp4 = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.5,
  config: {
    name: 'Скачать MP4',
    parameters: {
      method: 'GET',
      url: expr('{{ $json.video_uri }}'),
      authentication: 'genericCredentialType',
      genericAuthType: 'httpHeaderAuth',
      options: { response: { response: { responseFormat: 'file', outputPropertyName: 'video' } }, timeout: 180000 }
    },
    credentials: { httpHeaderAuth: { id: 'a1gKYqEJrOK6sguw', name: 'Gemini API' } },
    position: [3380, 100]
  },
  output: [{ video: 'binary' }]
});

const s3Upload = node({
  type: 'n8n-nodes-base.s3',
  version: 1,
  config: {
    name: 'Сохранить в Timeweb S3',
    parameters: {
      resource: 'file',
      operation: 'upload',
      bucketName: 'menaoffplan-media',
      fileName: expr("{{ $('Нормализовать бриф').item.json.file_key }}"),
      binaryData: true,
      binaryPropertyName: 'video',
      additionalFields: { acl: 'publicRead' }
    },
    credentials: { s3: { id: 'ygC0mmCU7vDdHok8', name: 'Timeweb S3' } },
    onError: 'continueRegularOutput',
    position: [3640, 0]
  },
  output: [{ success: true }]
});

const tgPreview = node({
  type: 'n8n-nodes-base.telegram',
  version: 1.2,
  config: {
    name: 'Превью в Telegram',
    parameters: {
      resource: 'message',
      operation: 'sendVideo',
      chatId: expr("{{ $('Нормализовать бриф').item.json.chat_id }}"),
      binaryData: true,
      binaryPropertyName: 'video',
      additionalFields: {
        caption: expr("🎬 VIDEO-PROD · {{ $('Нормализовать бриф').item.json.project }}\nМодель: {{ $('Нормализовать бриф').item.json.model }} · {{ $('Нормализовать бриф').item.json.orientation }} · {{ $('Нормализовать бриф').item.json.duration }} с\nКамера: {{ $('Разобрать JSON промпта').item.json.camera }} — {{ $('Разобрать JSON промпта').item.json.notes }}\nS3: {{ $('Нормализовать бриф').item.json.s3_url }}")
      }
    },
    credentials: { telegramApi: { id: '3NR12AA6JwJICobf', name: 'Monitor bot' } },
    position: [3640, 200]
  },
  output: [{ ok: true, result: { message_id: 1 } }]
});

const tgFail = node({
  type: 'n8n-nodes-base.telegram',
  version: 1.2,
  config: {
    name: 'Сообщить об отказе',
    parameters: {
      resource: 'message',
      operation: 'sendMessage',
      chatId: expr("{{ $('Нормализовать бриф').item.json.chat_id }}"),
      text: expr("⛔ VIDEO-PROD · {{ $('Нормализовать бриф').item.json.project }}: Veo не вернул видео.\nПричина: {{ $json.filtered }}\nКлючи ответа: {{ $json.response_keys }}"),
      additionalFields: { appendAttribution: false }
    },
    credentials: { telegramApi: { id: '3NR12AA6JwJICobf', name: 'Monitor bot' } },
    position: [3380, 400]
  },
  output: [{ ok: true }]
});

const note = sticky('## VIDEO-PROD — Нода 4–8 (Build Kit v1, Этап 1: фото → пролёт)\n\nВход: POST /webhook/video-prod\n{ project, image_url, brief, prompt?, orientation (9:16|16:9), model?, duration (4|6|8), chat_id? }\n\nЦепочка: бриф → фото → base64 → Claude пишет промпт → Veo 3.1 image-to-video (predictLongRunning) → poll каждые 15 с → MP4 → Timeweb S3 (video-prod/{project}/…) + превью в Telegram.\n\nПравило: модель только двигает камеру, объект не меняет. Ключ Gemini — в credential «Gemini API» (Header Auth). Бакет: menaoffplan-media.', [normalize, veoStart], { color: 4 });

export default workflow('video-prod-stage1', 'VIDEO-PROD — фото → пролёт (Veo 3.1)')
  .add(note)
  .add(briefIn)
  .to(normalize)
  .to(downloadPhoto)
  .to(photoToBase64)
  .to(claudePrompt)
  .to(parsePrompt)
  .to(veoStart)
  .to(saveOp)
  .to(waitPoll)
  .to(veoStatus)
  .to(isDone
    .onTrue(extractUri.to(hasVideo
      .onTrue(downloadMp4)
      .onFalse(tgFail)))
    .onFalse(waitPoll))
  .add(downloadMp4)
  .to(s3Upload)
  .add(downloadMp4)
  .to(tgPreview);
