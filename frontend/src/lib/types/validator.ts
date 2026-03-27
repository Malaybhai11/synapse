export type SourceType = 'notebook' | 'web' | 'both'

export interface ValidatorModels {
  analyzerModel: string
  redTeamModel: string
  strategistModel: string
}

export interface ValidatorRequest {
  idea: string
  sourceType: SourceType
  models: ValidatorModels
}

export interface Assumption {
  description: string
}

export interface Vulnerability {
  title: string
  description: string
  severity: 'High' | 'Medium' | 'Low'
  score: number
}

export interface Mitigation {
  description: string
  effort: 'High' | 'Medium' | 'Low'
}

export interface ValidatorResponse {
  idea: string
  assumptions: Assumption[]
  vulnerabilities: Vulnerability[]
  mitigations: Mitigation[]
  overallRiskScore: number
  analyzerThink?: string
  redTeamThink?: string
  strategistThink?: string
}
