import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';

/** Thin client for the R plumber API (gpcs/r/plumber.R), proxied at /rapi. */
export interface Row { requirement: string[]; source: string[]; components: string[]; status: string[] }
export interface CrosswalkResponse {
  crosswalk: { eligible: boolean[]; package: string[]; flags: string[]; rows: Row[];
               component_status: Record<string, { title: string[]; kind: string[]; coverage: number[]; missing: string[] }> };
  markdown: string[];
}
export interface Question { key: string[]; prompt: string[]; why: string[]; required: boolean[] }

@Injectable({ providedIn: 'root' })
export class GpcsService {
  private http = inject(HttpClient);
  private base = '/rapi';
  health() { return this.http.get<{ ok: boolean[]; engine: string[] }>(`${this.base}/health`); }
  intake(type: string) { return this.http.get<Question[]>(`${this.base}/intake/${type}`); }
  crosswalk(text: string, org: string, program: string) {
    return this.http.post<CrosswalkResponse>(`${this.base}/crosswalk`, { text }, { params: { org, program } });
  }
}
