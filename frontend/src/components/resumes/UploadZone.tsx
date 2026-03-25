"use client";

import { useCallback, useState } from "react";
import { Upload, FileText, Loader2, AlertCircle, CheckCircle } from "lucide-react";
import { api } from "@/lib/api";
import { toast } from "sonner";

interface UploadZoneProps {
  roleId: string;
  onUploadComplete: () => void;
}

export function UploadZone({ roleId, onUploadComplete }: UploadZoneProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadResults, setUploadResults] = useState<any[]>([]);

  const handleFiles = useCallback(
    async (files: FileList | File[]) => {
      const validFiles = Array.from(files).filter((f) => {
        const ext = f.name.toLowerCase();
        return (
          ext.endsWith(".pdf") ||
          ext.endsWith(".docx") ||
          ext.endsWith(".doc") ||
          ext.endsWith(".rtf") ||
          ext.endsWith(".txt") ||
          ext.endsWith(".md") ||
          ext.endsWith(".html") ||
          ext.endsWith(".htm") ||
          ext.endsWith(".png") ||
          ext.endsWith(".jpg") ||
          ext.endsWith(".jpeg") ||
          ext.endsWith(".tiff") ||
          ext.endsWith(".bmp") ||
          ext.endsWith(".heic") ||
          ext.endsWith(".eml") ||
          ext.endsWith(".msg")
        );
      });

      if (validFiles.length === 0) {
        toast.error("Unsupported file type. Upload PDF, Word, text, images, or email files.");
        return;
      }

      if (validFiles.length !== Array.from(files).length) {
        toast.warning("Some files were skipped (unsupported file types)");
      }

      setUploading(true);
      setUploadResults([]);
      const results: any[] = [];

      for (const file of validFiles) {
        try {
          const result = await api.uploadResume(roleId, file);
          results.push({ name: file.name, ...result });
        } catch (e: any) {
          results.push({ name: file.name, status: "error", message: e.message });
        }
      }

      setUploadResults(results);
      setUploading(false);
      onUploadComplete();

      const successCount = results.filter((r) => r.status !== "error" && !r.duplicate).length;
      const dupeCount = results.filter((r) => r.duplicate).length;
      if (successCount > 0) {
        toast.success(`${successCount} resume${successCount > 1 ? "s" : ""} uploaded`);
      }
      if (dupeCount > 0) {
        toast.warning(`${dupeCount} duplicate${dupeCount > 1 ? "s" : ""} detected`);
      }
    },
    [roleId, onUploadComplete]
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      handleFiles(e.dataTransfer.files);
    },
    [handleFiles]
  );

  return (
    <div className="space-y-3">
      <div
        className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors cursor-pointer ${
          isDragging
            ? "border-primary bg-primary/5"
            : "border-muted-foreground/25 hover:border-primary/50"
        }`}
        onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        onClick={() => {
          const input = document.createElement("input");
          input.type = "file";
          input.accept = ".pdf,.docx,.doc,.rtf,.txt,.md,.html,.htm,.png,.jpg,.jpeg,.tiff,.bmp,.heic,.eml,.msg";
          input.multiple = true;
          input.onchange = (e) => {
            const files = (e.target as HTMLInputElement).files;
            if (files) handleFiles(files);
          };
          input.click();
        }}
      >
        {uploading ? (
          <Loader2 className="h-8 w-8 mx-auto text-primary animate-spin mb-2" />
        ) : (
          <Upload className="h-8 w-8 mx-auto text-muted-foreground mb-2" />
        )}
        <p className="text-sm font-medium">
          {uploading ? "Uploading..." : "Drop resumes here or click to browse"}
        </p>
        <p className="text-xs text-muted-foreground mt-1">
          PDF, Word, text/markdown, HTML, images, and email files supported
        </p>
      </div>

      {uploadResults.length > 0 && (
        <div className="space-y-1">
          {uploadResults.map((r, i) => (
            <div key={i} className="flex items-center gap-2 text-xs px-2 py-1 rounded bg-muted">
              {r.status === "error" ? (
                <AlertCircle className="h-3 w-3 text-destructive shrink-0" />
              ) : r.duplicate ? (
                <AlertCircle className="h-3 w-3 text-amber-500 shrink-0" />
              ) : (
                <CheckCircle className="h-3 w-3 text-green-500 shrink-0" />
              )}
              <span className="truncate">{r.name}</span>
              <span className="text-muted-foreground ml-auto shrink-0">
                {r.status === "error" ? r.message : r.duplicate ? "Duplicate" : r.status}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
