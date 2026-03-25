"use client";

import Link from "next/link";
import { useParams, usePathname } from "next/navigation";
import { cn } from "@/lib/utils";

export default function RoleLayout({ children }: { children: React.ReactNode }) {
  const params = useParams();
  const pathname = usePathname();
  const roleId = params.id as string;

  const tabs = [
    { href: `/roles/${roleId}`, label: "Candidates" },
    { href: `/roles/${roleId}/settings`, label: "Settings" },
  ];

  return (
    <div>
      <div className="border-b bg-card px-6">
        <nav className="flex gap-4">
          {tabs.map((tab) => (
            <Link
              key={tab.href}
              href={tab.href}
              className={cn(
                "py-3 text-sm border-b-2 transition-colors",
                pathname === tab.href
                  ? "border-primary text-primary font-medium"
                  : "border-transparent text-muted-foreground hover:text-foreground"
              )}
            >
              {tab.label}
            </Link>
          ))}
        </nav>
      </div>
      {children}
    </div>
  );
}
