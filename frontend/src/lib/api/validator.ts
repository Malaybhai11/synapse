import apiClient from './client'
import { ValidatorRequest, ValidatorResponse } from '@/lib/types/validator'

export const validatorApi = {
  evaluate: async (params: ValidatorRequest): Promise<ValidatorResponse> => {
    const response = await apiClient.post<ValidatorResponse>('/validator/evaluate', params)
    return response.data
  }
}
