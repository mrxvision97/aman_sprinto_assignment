"use client";

import { usePolling } from "@/hooks/use-polling";
import { Header } from "@/components/layout/Header";
import { RoleCard } from "@/components/roles/RoleCard";
import { Button } from "@/components/ui/button";
import Link from "next/link";
import { Plus, Briefcase } from "lucide-react";

export default function Dashboard() {
  const { data: roles, error, isLoading } = usePolling<any[]>("/api/roles", 5000);

  return (
    <div>
      <Header title="Dashboard" subtitle="Manage your open roles and screen candidates" />
      <div className="p-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <p className="text-sm text-muted-foreground">
              {roles?.length || 0} active role{roles?.length !== 1 ? "s" : ""}
            </p>
          </div>
          <Link href="/roles/new">
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              New Role
            </Button>
          </Link>
        </div>

        {isLoading && (
          <div className="flex items-center justify-center py-20">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
          </div>
        )}

        {error && (
          <div className="text-center py-20">
            <p className="text-destructive">Failed to load roles. Is the backend running?</p>
            <p className="text-sm text-muted-foreground mt-2">{error.message}</p>
          </div>
        )}

        {roles && roles.length === 0 && (
          <div className="text-center py-20 border-2 border-dashed rounded-lg">
            <Briefcase className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
            <h3 className="font-semibold mb-2">No roles yet</h3>
            <p className="text-sm text-muted-foreground mb-4">
              Create your first role to start screening resumes
            </p>
            <Link href="/roles/new">
              <Button>
                <Plus className="h-4 w-4 mr-2" />
                Create Role
              </Button>
            </Link>
          </div>
        )}

        {roles && roles.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {roles.map((role: any) => (
              <RoleCard key={role.id} role={role} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
