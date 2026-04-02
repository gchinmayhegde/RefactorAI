import { create } from 'zustand'

const useMigrationStore = create((set, get) => ({
  legacyCode: `# Legacy Python 2.7 Example
def process_user_data(users):
    result = []
    for i in range(len(users)):
        u = users[i]
        if u != None:
            if type(u) == dict:
                if u.has_key('name') and u.has_key('age'):
                    if u['age'] >= 0 and u['age'] <= 150:
                        name = u['name'].encode('utf-8')
                        result.append({
                            'name': name,
                            'age': u['age'],
                            'is_adult': True if u['age'] >= 18 else False
                        })
    return result`,
  modernCode: '',
  sourceLanguage: 'python',
  targetLanguage: 'python',
  metrics: null,
  isRefactoring: false,
  error: null,
  streamController: null,

  setLegacyCode: (code) => set({ legacyCode: code }),
  setModernCode: (code) => set({ modernCode: code }),
  setSourceLanguage: (lang) => set({ sourceLanguage: lang }),
  setTargetLanguage: (lang) => set({ targetLanguage: lang }),
  setMetrics: (metrics) => set({ metrics }),
  setIsRefactoring: (val) => set({ isRefactoring: val }),
  setError: (error) => set({ error }),

  appendModernCode: (chunk) =>
    set((state) => ({ modernCode: state.modernCode + chunk })),

  startRefactor: async () => {
    const { legacyCode, sourceLanguage, targetLanguage } = get()

    const prev = get().streamController
    if (prev) prev.abort()

    const controller = new AbortController()
    set({
      isRefactoring: true,
      modernCode: '',
      metrics: null,
      error: null,
      streamController: controller,
    })

    try {
      const response = await fetch('http://localhost:8000/api/refactor', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          legacy_code: legacyCode,
          source_language: sourceLanguage,
          target_language: targetLanguage,
        }),
        signal: controller.signal,
      })

      if (!response.ok) {
        throw new Error(`Server error: ${response.status} ${response.statusText}`)
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''
      let currentEvent = null

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop()

        for (const line of lines) {
          const trimmed = line.trim()
          if (!trimmed) {
            currentEvent = null
            continue
          }

          if (trimmed.startsWith('event:')) {
            currentEvent = trimmed.slice(6).trim()
          } else if (trimmed.startsWith('data:')) {
            const dataStr = trimmed.slice(5).trim()
            try {
              const data = JSON.parse(dataStr)
              if (currentEvent === 'code' && data.chunk) {
                get().appendModernCode(data.chunk)
              } else if (currentEvent === 'metrics') {
                set({ metrics: data })
              } else if (currentEvent === 'error') {
                set({ error: data.error || 'An unknown error occurred.' })
              }
            } catch {
              // ignore non-JSON
            }
          }
        }
      }
    } catch (err) {
      if (err.name !== 'AbortError') {
        set({
          error: err.message || 'Failed to connect to the RefactorAI backend.',
        })
      }
    } finally {
      set({ isRefactoring: false, streamController: null })
    }
  },

  cancelRefactor: () => {
    const { streamController } = get()
    if (streamController) {
      streamController.abort()
      set({ isRefactoring: false, streamController: null })
    }
  },
}))

export default useMigrationStore