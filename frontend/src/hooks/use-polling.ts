import useSWR from "swr";
import { fetcher } from "@/lib/api";

export function usePolling<T>(path: string | null, intervalMs = 3000) {
  return useSWR<T>(path, fetcher, {
    refreshInterval: intervalMs,
    revalidateOnFocus: true,
  });
}
