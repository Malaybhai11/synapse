import { useMutation } from '@tanstack/react-query'
import { toast } from 'sonner'
import { useTranslation } from '@/lib/hooks/use-translation'
import { getApiErrorKey } from '@/lib/utils/error-handler'
import { hypothesisApi } from '@/lib/api/hypothesis'
import { HypothesisRequest, HypothesisResponse } from '@/lib/types/hypothesis'

export function useHypothesis() {
  const { t } = useTranslation()
  
  const mutation = useMutation({
    mutationFn: async (params: HypothesisRequest) => {
      // In development or if the backend endpoint isn't ready yet, this might fail.
      // We will handle the real logic in the backend next.
      return await hypothesisApi.evaluate(params)
    },
    onError: (error: Error) => {
      toast.error('Hypothesis Evaluation Failed', {
        description: t(getApiErrorKey(error.message)) || error.message
      })
    }
  })

  return {
    evaluateHypothesis: mutation.mutate,
    data: mutation.data,
    isPending: mutation.isPending,
    isError: mutation.isError,
    error: mutation.error
  }
}
