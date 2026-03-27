export interface HypothesisRequest {
  query: string;
  includeWebSearch?: boolean;
  models: {
    proponentModel: string;
    opponentModel: string;
    judgeModel: string;
  };
}

export interface EvidenceItem {
  id: string;
  sourceType: 'notebook' | 'web';
  title: string;
  snippet: string;
  url?: string;
  score: number;
}

export interface HypothesisResponse {
  hypothesis: string;
  confidenceScore: number; // 0-100
  proponentEvidence: EvidenceItem[];
  opponentEvidence: EvidenceItem[];
  judgeSynthesis: string;
}
