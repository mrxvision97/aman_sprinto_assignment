"use client";

import { Badge } from "@/components/ui/badge";
import { Loader2 } from "lucide-react";

const statusConfig: Record<string, { label: string; variant: "default" | "secondary" | "destructive" | "outline"; spin?: boolean }> = {
  pending: { label: "Pending", variant: "outline" },
  processing: { label: "Processing", variant: "secondary", spin: true },
  parsing: { label: "Parsing", variant: "secondary", spin: true },
  extracting: { label: "Extracting", variant: "secondary", spin: true },
  scoring: { label: "Scoring", variant: "secondary", spin: true },
  scored: { label: "Scored", variant: "default" },
  error: { label: "Error", variant: "destructive" },
  duplicate: { label: "Duplicate", variant: "outline" },
};

export function StatusBadge({ status }: { status: string }) {
  const config = statusConfig[status] || { label: status, variant: "outline" as const };

  return (
    <Badge variant={config.variant} className="text-xs gap-1">
      {config.spin && <Loader2 className="h-3 w-3 animate-spin" />}
      {config.label}
    </Badge>
  );
}
