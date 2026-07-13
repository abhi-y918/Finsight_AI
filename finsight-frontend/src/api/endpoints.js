import client from './client'

export const analyzeStatement = async (file) => {
  const formData = new FormData()
  formData.append('file', file)

  const response = await client.post('/analyze', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
  return response.data
}
