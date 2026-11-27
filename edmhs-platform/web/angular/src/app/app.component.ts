import { Component, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { GpcsService, CrosswalkResponse, Question } from './gpcs.service';

@Component({
  selector: 'gpcs-root',
  standalone: true,
  imports: [FormsModule],
  template: `
  <header><div class="wrap">
    <a class="brand" href="https://edmhs.org">EDMHS<span>.org</span></a>
    <nav><a href="https://edmhs.org">Home</a><a href="https://ict.edmhs.us">ICT</a><a href="https://kata.edmhs.us">KATA</a></nav>
  </div></header>
  <main class="wrap">
    <h1>Grant Studio <small>GPCS · R engine {{ engineOk() ? '● online' : '○ offline' }}</small></h1>
    <div class="row">
      <label>Applicant
        <select [(ngModel)]="org" (ngModelChange)="loadIntake()">
          <option value="edmhs_org">EDMHS.org (nonprofit)</option>
          <option value="edm_health_services_llc">EDM Health Services, LLC (for-profit)</option>
        </select></label>
      <label>Program
        <select [(ngModel)]="program"><option value="ict">Inner Combat Training</option><option value="pmsg">PMSG</option><option value="kata">KATA</option></select></label>
    </div>

    <section>
      <h2>1 · Read the solicitation</h2>
      <p class="muted">Paste the solicitation text (the R engine also reads PDFs server-side via pdftools).</p>
      <textarea [(ngModel)]="text" rows="8" placeholder="Paste Grants.gov listing / NOFO text"></textarea>
      <div class="row"><button (click)="run()" [disabled]="!text || busy()">{{ busy() ? 'Reading…' : 'Analyze + crosswalk' }}</button>
        @if (error()) { <span class="error">{{ error() }}</span> }</div>
      @if (result(); as r) {
        <p>Package: <b>{{ r.crosswalk.package[0] }}</b> · Eligible: <b>{{ r.crosswalk.eligible[0] ? 'yes' : 'NO' }}</b></p>
        <ul class="flags">@for (f of r.crosswalk.flags; track $index) { <li [class.blocker]="f.startsWith('BLOCKER')">{{ f }}</li> }</ul>
        <div class="tbl"><table>
          <thead><tr><th>#</th><th>Requirement</th><th>Components</th><th>Status</th></tr></thead>
          <tbody>@for (row of r.crosswalk.rows; track $index) {
            <tr><td>{{ $index + 1 }}</td><td>{{ row.requirement[0] }}</td><td>{{ row.components.join(', ') || '—' }}</td><td>{{ row.status[0] }}</td></tr>
          }</tbody>
        </table></div>
      }
    </section>

    <section>
      <h2>2 · Applicant intake ({{ org === 'edmhs_org' ? 'nonprofit' : 'for-profit' }})</h2>
      <form class="intake">
        @for (q of questions(); track q.key[0]) {
          <label>{{ q.prompt[0] }} @if (q.required[0]) {<em>*</em>}<small>{{ q.why[0] }}</small><input [name]="q.key[0]"></label>
        }
      </form>
    </section>
  </main>`,
})
export class AppComponent {
  private api = inject(GpcsService);
  org = 'edmhs_org';
  program = 'ict';
  text = '';
  busy = signal(false);
  error = signal('');
  engineOk = signal(false);
  result = signal<CrosswalkResponse | null>(null);
  questions = signal<Question[]>([]);

  constructor() {
    this.api.health().subscribe({ next: h => this.engineOk.set(!!h.ok?.[0]), error: () => this.engineOk.set(false) });
    this.loadIntake();
  }
  loadIntake() {
    const type = this.org === 'edmhs_org' ? 'nonprofit' : 'for_profit';
    this.api.intake(type).subscribe({ next: q => this.questions.set(q), error: () => this.questions.set([]) });
  }
  run() {
    this.busy.set(true); this.error.set('');
    this.api.crosswalk(this.text, this.org, this.program).subscribe({
      next: r => { this.result.set(r); this.busy.set(false); },
      error: e => { this.error.set(`R API error ${e.status}`); this.busy.set(false); },
    });
  }
}
