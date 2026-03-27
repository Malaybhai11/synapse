import apiClient from './client'
import { HypothesisRequest, HypothesisResponse } from '@/lib/types/hypothesis'

export const hypothesisApi = {
  evaluate: async (params: HypothesisRequest): Promise<HypothesisResponse> => {
    const response = await apiClient.post<HypothesisResponse>('/hypothesis/evaluate', params)
    return response.data
  }
}
