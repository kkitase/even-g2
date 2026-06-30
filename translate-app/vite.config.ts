import { defineConfig, loadEnv } from 'vite'
import { handleApi } from './server/api'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  // server/api.ts は process.env から読むので、ここで橋渡しする
  if (env.GEMINI_API_KEY && !process.env.GEMINI_API_KEY) {
    process.env.GEMINI_API_KEY = env.GEMINI_API_KEY
  }

  return {
    server: {
      host: true,
      port: 5173,
    },
    plugins: [
      {
        name: 'eveng2-translate-api',
        configureServer(server) {
          server.middlewares.use((req, res, next) => {
            const url = req.url ?? ''
            if (url.startsWith('/api/')) {
              handleApi(req, res, next).catch(next)
              return
            }
            next()
          })
        },
      },
    ],
  }
})
