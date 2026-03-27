import { useMutation } from '@tanstack/react-query'
import { ValidatorRequest, ValidatorResponse } from '@/lib/types/validator'
import { validatorApi } from '@/lib/api/validator'

export function useValidator() {
  const { mutate: runValidator, data, isPending, isError, error, reset } = useMutation({
    mutationFn: (params: ValidatorRequest): Promise<ValidatorResponse> => validatorApi.evaluate(params),
  })

  return { runValidator, data, isPending, isError, error: error as Error | null, reset }
}
