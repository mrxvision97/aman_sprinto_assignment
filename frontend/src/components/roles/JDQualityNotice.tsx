"use client";

import { AlertTriangle, Info, XCircle } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const iconMap: Record<string, any> = {
  error: XCircle,
  warning: AlertTriangle,
  info: Info,
};

const colorMap: Record<string, string> = {
  error: "text-destructive",
  warning: "text-amber-500",
  info: "text-blue-500",
};

const bgMap: Record<string, string> = {
  error: "bg-destructive/10",
  warning: "bg-amber-500/10",
  info: "bg-blue-500/10",
};

export function JDQualityNotice({ report }: { report: any }) {
  if (!report?.flags || report.flags.length === 0) {
    return (
      <Card className="border-green-200 bg-green-50">
        <CardContent className="pt-4">
          <p className="text-sm text-green-700">
            JD quality looks good. No issues detected.
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-sm font-medium">JD Quality Analysis</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {report.flags.map((flag: any, i: number) => {
          const Icon = iconMap[flag.severity] || Info;
          return (
            <div key={i} className={`p-3 rounded-md ${bgMap[flag.severity] || bgMap.info}`}>
              <div className="flex items-start gap-2">
                <Icon className={`h-4 w-4 mt-0.5 shrink-0 ${colorMap[flag.severity] || colorMap.info}`} />
                <div>
                  <p className="text-sm font-medium">{flag.flag}</p>
                  {flag.suggestion && (
                    <p className="text-xs text-muted-foreground mt-1">{flag.suggestion}</p>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </CardContent>
    </Card>
  );
}
