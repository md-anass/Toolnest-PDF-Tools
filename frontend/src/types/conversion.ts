export type ConversionStage =
  | 'idle'
  | 'uploading'
  | 'analyzing'
  | 'extracting'
  | 'running_ocr'
  | 'reconstructing'
  | 'completed'
  | 'failed';

export type JobStatus = 'pending' | 'processing' | 'completed' | 'failed';

export interface PDFMetadata {
  title?: string | null;
  author?: string | null;
  subject?: string | null;
  creator?: string | null;
  producer?: string | null;
  creation_date?: string | null;
  mod_date?: string | null;
}

export interface DocumentAnalysis {
  page_count: number;
  total_characters: number;
  total_words: number;
  total_images: number;
  total_tables: number;
  is_scanned: boolean;
  scanned_pages: number[];
  selectable_pages: number[];
  ocr_recommended: boolean;
  average_text_density: number;
  metadata: PDFMetadata;
}

export interface ExtractedElements {
  paragraphs: number;
  headings: number;
  tables: number;
  images: number;
  lists: number;
}

export interface ConversionResult {
  file_id: string;
  job_id: string;
  original_filename: string;
  docx_filename: string;
  download_url: string;
  page_count: number;
  is_scanned: boolean;
  ocr_used: boolean;
  extracted_elements: ExtractedElements;
  duration_seconds: number;
  file_size_bytes: number;
  completed_at: string;
}

export interface JobStatusResponse {
  job_id: string;
  status: JobStatus;
  stage: ConversionStage;
  stage_message: string;
  progress: number;
  error_message?: string | null;
  result?: ConversionResult | null;
  analysis?: DocumentAnalysis | null;
  created_at: string;
  updated_at: string;
}

export interface UploadResponse {
  job_id: string;
  file_id: string;
  original_filename: string;
  file_size: number;
  status: JobStatus;
  stage: ConversionStage;
  message: string;
}

export interface FileItem {
  file: File;
  name: string;
  size: number;
  pageCount?: number;
  analysis?: DocumentAnalysis;
  isAnalyzing?: boolean;
}
