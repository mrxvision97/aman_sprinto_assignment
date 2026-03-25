"use client";

import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Users, Star } from "lucide-react";

export function RoleCard({ role }: { role: any }) {
  return (
    <Link href={`/roles/${role.id}`}>
      <Card className="hover:shadow-md transition-shadow cursor-pointer">
        <CardHeader className="pb-3">
          <div className="flex items-start justify-between">
            <CardTitle className="text-base">{role.title}</CardTitle>
            <Badge variant={role.status === "active" ? "default" : "secondary"}>
              {role.status}
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-4 text-sm text-muted-foreground">
            <div className="flex items-center gap-1">
              <Users className="h-4 w-4" />
              <span>{role.resume_count || 0} resumes</span>
            </div>
            <div className="flex items-center gap-1">
              <Star className="h-4 w-4" />
              <span>{role.scored_count || 0} scored</span>
            </div>
            {role.avg_score != null && (
              <div className="ml-auto font-medium text-foreground">
                Avg: {Number(role.avg_score).toFixed(1)}
              </div>
            )}
          </div>
          {role.blind_mode && (
            <Badge variant="outline" className="mt-3 text-xs">
              Blind Mode
            </Badge>
          )}
        </CardContent>
      </Card>
    </Link>
  );
}
