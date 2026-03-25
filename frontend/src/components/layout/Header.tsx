"use client";

export function Header({ title, subtitle }: { title: string; subtitle?: string }) {
  return (
    <div className="border-b bg-card px-6 py-4">
      <h1 className="text-xl font-semibold">{title}</h1>
      {subtitle && <p className="text-sm text-muted-foreground mt-0.5">{subtitle}</p>}
    </div>
  );
}
