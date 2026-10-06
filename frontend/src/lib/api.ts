import {
  UploadResponse,
  JobStatusResponse,
  DocumentAnalysis,
} from '@/types/conversion';
import type { DocumentToolOperation } from '@/components/DocumentTools';

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export class ApiError extends Error {
  statusCode?: number;
  constructor(message: string, statusCode?: number) {
    super(message);
    this.name = 'ApiError';
    this.statusCode = statusCode;
  }
}

/** Upload documents to a PDF utility endpoint and download its result. */
export async function runDocumentTool(
  operation: DocumentToolOperation,
  files: File[]
): Promise<void> {
  const formData = new FormData();
  files.forEach((file) => formData.append('files', file));

  const response = await fetch(`${API_BASE_URL}/api/tools/${operation}`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    let message = 'Unable to process these files.';
    try {
      const data = await response.json();
      message = data.message || data.detail || message;
    } catch {
      // Keep the fallback message for non-JSON responses.
    }
    throw new ApiError(message, response.status);
  }

  const blob = await response.blob();
  const disposition = response.headers.get('Content-Disposition') || '';
  const filename = disposition.match(/filename="?([^";]+)"?/i)?.[1] || 'document.pdf';
  const downloadUrl = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = downloadUrl;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.setTimeout(() => URL.revokeObjectURL(downloadUrl), 1000);
}

/**
 * Perform initial health check to verify backend connection.
 */
export async function checkBackendHealth() {
  try {
    const res = await fetch(`${API_BASE_URL}/api/health`, {
      method: 'GET',
      headers: { Accept: 'application/json' },
    });
    if (!res.ok) return null;
    return await res.json();
  } catch (err) {
    console.warn('Backend not yet reachable on', API_BASE_URL, err);
    return null;
  }
}

/**
 * Pre-analyze an uploaded PDF to read page count and scan indicators.
 */
export async function analyzePDFFile(file: File): Promise<DocumentAnalysis> {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${API_BASE_URL}/api/analyze`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    let errMsg = 'Failed to analyze PDF file.';
    try {
      const data = await response.json();
      errMsg = data.message || data.detail || errMsg;
    } catch {
      // ignore
    }
    throw new ApiError(errMsg, response.status);
  }

  return response.json();
}

/**
 * Upload PDF and trigger asynchronous conversion job.
 */
export async function uploadAndStartConversion(
  file: File,
  onUploadProgress?: (percent: number) => void
): Promise<UploadResponse> {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    const formData = new FormData();
    formData.append('file', file);

    xhr.open('POST', `${API_BASE_URL}/api/convert`);

    if (xhr.upload && onUploadProgress) {
      xhr.upload.onprogress = (event) => {
        if (event.lengthComputable) {
          const percent = Math.round((event.loaded / event.total) * 100);
          onUploadProgress(percent);
        }
      };
    }

    xhr.onload = () => {
      try {
        const data = JSON.parse(xhr.responseText);
        if (xhr.status >= 200 && xhr.status < 300) {
          resolve(data as UploadResponse);
        } else {
          const msg = data.message || data.detail || 'Conversion upload failed.';
          reject(new ApiError(msg, xhr.status));
        }
      } catch {
        reject(new ApiError('Invalid response from server.', xhr.status));
      }
    };

    xhr.onerror = () => {
      reject(
        new ApiError(
          'Network connection error. Please ensure the backend server is running.'
        )
      );
    };

    xhr.send(formData);
  });
}

/**
 * Poll job status by job ID.
 */
export async function fetchJobStatus(jobId: string): Promise<JobStatusResponse> {
  const response = await fetch(`${API_BASE_URL}/api/convert/${jobId}`, {
    method: 'GET',
    headers: { Accept: 'application/json' },
  });

  if (!response.ok) {
    let errMsg = 'Failed to fetch job progress.';
    try {
      const data = await response.json();
      errMsg = data.message || data.detail || errMsg;
    } catch {
      // ignore
    }
    throw new ApiError(errMsg, response.status);
  }

  return response.json();
}

/**
 * Build direct download URL for a converted file.
 */
export function buildDownloadUrl(fileId: string): string {
  return `${API_BASE_URL}/api/download/${fileId}`;
}

/**
 * Delete temporary files immediately from backend storage.
 */
export async function deleteTemporaryFile(fileId: string): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/files/${fileId}`, {
      method: 'DELETE',
    });
    return res.ok;
  } catch (err) {
    console.warn('Failed to delete file from backend:', err);
    return false;
  }
}
