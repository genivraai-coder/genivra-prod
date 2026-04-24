import Link from "next/link";
import { ArrowRight, ArrowUpRight } from "lucide-react";
import FloatingKeywords from "@/components/FloatingKeywords";
import { Badge } from "@/components/ui/badge";
import { buttonVariants } from "@/components/ui/button";
import { FeatureGrid, HOME_FEATURES } from "@/components/ui/feature";
import ResearchSupportedBy from "@/components/ResearchSupportedBy";

const METRICS = [
  { value: "450+", label: "Trials Managed" },
  { value: "40%", label: "Faster Processing" },
  { value: "12M+", label: "Data Points" },
  { value: "99%", label: "Retention Rate" },
];

const INDICATIONS = [
  "Alzheimer's",
  "Parkinson's",
  "ALS",
  "Depression",
  "Schizophrenia",
  "Multiple Sclerosis",
  "Huntington's",
  "Epilepsy",
  "Bipolar",
  "PTSD",
  "Migraine",
  "Stroke",
];

const CAPABILITIES = [
  "Biomarker Validation",
  "Imaging Signals",
  "Phase II Transition",
  "Patient Enrichment",
  "Regulatory Readiness",
  "Protocol Optimization",
];

export default function Home() {
  return (
    <div className="overflow-hidden">
      {/* HERO */}
      <section className="relative min-h-[92vh] overflow-hidden pt-28 sm:pt-32">
        <FloatingKeywords />
        <div className="pointer-events-none absolute inset-0 opacity-[0.55]">
          <div className="absolute left-1/2 top-[30%] h-[560px] w-[980px] -translate-x-1/2 rounded-full bg-sky-500/[0.07] blur-[130px]" />
        </div>

        <div className="relative z-10 mx-auto flex max-w-[1600px] flex-col px-6 sm:px-8">
          <div className="mb-8 flex items-center gap-2">
            <Badge variant="live">
              <span className="relative mr-1 flex h-1.5 w-1.5">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400/70" />
                <span className="relative inline-flex h-1.5 w-1.5 rounded-full bg-emerald-500" />
              </span>
              Now in Private Alpha
            </Badge>
            <span className="eyebrow hidden sm:inline">
              Clinical Diligence Platform for Neurodegenerative Drug Programs
            </span>
          </div>

          <h1 className="display-xxl mb-6 text-[18vw] leading-[0.92] text-white sm:text-[14vw] lg:text-[11vw]">
            Genivra<span className="text-sky-400/90">.</span>
          </h1>

          <div className="grid gap-10 border-t border-white/[0.06] pt-10 md:grid-cols-12">
            <div className="md:col-span-7 lg:col-span-8">
              <p className="max-w-3xl text-2xl leading-[1.2] tracking-tight text-white sm:text-3xl md:text-[2.25rem]">
                CNS Trials, <span className="text-slate-500">Decoded by AI.</span>
              </p>
              <p className="mt-6 max-w-2xl text-[15px] leading-relaxed text-slate-400 sm:text-base">
                Analyze CNS clinical trials before they fail. Built for biotech investors, BD teams, and CNS research groups evaluating neurodegenerative pipelines.
              </p>
              <div className="mt-10 flex flex-wrap items-center gap-3">
                <a
                  href="#join-waitlist"
                  className={buttonVariants({ variant: "default", size: "lg" })}
                >
                  Request Early Access
                  <ArrowRight className="size-4" />
                </a>
                <Link
                  href="/PlatformFeatures"
                  className={buttonVariants({ variant: "outline", size: "lg" })}
                >
                  Explore Platform
                </Link>
              </div>
            </div>
            <aside className="md:col-span-5 lg:col-span-4">
              <p className="eyebrow mb-4">Focus</p>
              <ul className="divide-y divide-white/[0.06] border-y border-white/[0.06]">
                {CAPABILITIES.slice(0, 5).map((c) => (
                  <li
                    key={c}
                    className="flex items-center justify-between py-3 text-[14px] text-slate-300"
                  >
                    <span>{c}</span>
                    <ArrowUpRight className="size-3.5 text-slate-600" />
                  </li>
                ))}
              </ul>
            </aside>
          </div>
        </div>
      </section>

      <ResearchSupportedBy />

      {/* INDICATION MARQUEE */}
      <section className="relative border-y border-white/[0.06] bg-[var(--surface)]/60 py-5 sm:py-6">
        <div className="flex gap-14 overflow-hidden whitespace-nowrap">
          <div className="flex animate-marquee gap-14 whitespace-nowrap">
            {[...INDICATIONS, ...INDICATIONS].map((ind, i) => (
              <span
                key={`${ind}-${i}`}
                className="flex items-center gap-14 text-[13px] font-medium uppercase tracking-[0.2em] text-slate-500"
              >
                {ind}
                <span className="h-1 w-1 rounded-full bg-slate-700" />
              </span>
            ))}
          </div>
        </div>
      </section>

      {/* FEATURED — cards */}
      <section className="relative py-24 sm:py-32">
        <div className="mx-auto max-w-[1600px] px-6 sm:px-8">
          <div className="mb-14 flex flex-col gap-4 md:mb-20 md:flex-row md:items-end md:justify-between">
            <div>
              <p className="eyebrow mb-3">Featured — Capabilities</p>
              <h2 className="display-xl max-w-3xl text-4xl text-white sm:text-5xl md:text-6xl">
                Built for the future of clinical intelligence.
              </h2>
            </div>
            <p className="max-w-md text-[15px] leading-relaxed text-slate-400">
              Genivra models Phase II transition risk using imaging and biomarker validation signals across neurodegenerative programs.
            </p>
          </div>

          <FeatureGrid items={HOME_FEATURES} />
        </div>
      </section>

      {/* STATEMENT + METRICS */}
      <section className="relative border-y border-white/[0.06] bg-[var(--surface)]/40 py-24 sm:py-32">
        <div className="mx-auto max-w-[1600px] px-6 sm:px-8">
          <p className="eyebrow mb-6">Built for</p>
          <h2 className="display-xxl max-w-6xl text-5xl text-white sm:text-7xl lg:text-[6.5rem]">
            the future of{" "}
            <span className="text-slate-500">clinical intelligence.</span>
          </h2>
          <p className="mt-8 max-w-2xl text-[15px] leading-relaxed text-slate-400">
            Genivra models Phase II transition risk using imaging and biomarker validation signals across neurodegenerative programs.
          </p>

          <div className="mt-16 grid grid-cols-2 gap-px overflow-hidden rounded-2xl bg-white/[0.06] sm:mt-20 lg:grid-cols-4">
            {METRICS.map((m) => (
              <div
                key={m.label}
                className="flex flex-col justify-between gap-8 bg-[var(--background)] p-6 sm:p-8 lg:p-10"
              >
                <span className="eyebrow">{m.label}</span>
                <div className="display-xl text-4xl text-white sm:text-5xl lg:text-6xl">
                  {m.value}
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* SECONDARY MARQUEE - capabilities */}
      <section className="border-b border-white/[0.06] py-6 sm:py-8">
        <div className="overflow-hidden whitespace-nowrap">
          <div className="flex animate-marquee-slow gap-10 whitespace-nowrap">
            {[...CAPABILITIES, ...CAPABILITIES, ...CAPABILITIES].map((c, i) => (
              <span
                key={`${c}-${i}`}
                className="display-xl flex items-center gap-10 text-4xl text-slate-700 sm:text-5xl"
              >
                {c}
                <span className="h-1.5 w-1.5 rounded-full bg-slate-800" />
              </span>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="relative py-24 sm:py-32">
        <div className="mx-auto max-w-[1600px] px-6 sm:px-8">
          <div className="relative overflow-hidden rounded-3xl border border-white/[0.08] bg-gradient-to-br from-sky-500/[0.08] via-white/[0.02] to-transparent px-8 py-16 sm:px-14 sm:py-20 md:px-20 md:py-24">
            <div className="pointer-events-none absolute -right-20 -top-20 h-80 w-80 rounded-full bg-sky-500/20 blur-[120px]" />
            <div className="relative z-10 max-w-3xl">
              <p className="eyebrow mb-5">Get Started</p>
              <h2 className="display-xl text-4xl text-white sm:text-5xl md:text-6xl">
                Ready to accelerate your research?
              </h2>
              <p className="mt-6 max-w-xl text-[15px] leading-relaxed text-slate-400 sm:text-base">
                Join leading biotech teams who trust Genivra for their critical intelligence needs.
              </p>
              <div className="mt-10 flex flex-wrap items-center gap-3">
                <a
                  href="#join-waitlist"
                  className={buttonVariants({ variant: "default", size: "lg" })}
                >
                  Start Free Trial
                </a>
                <a
                  href="#join-waitlist"
                  className={buttonVariants({ variant: "outline", size: "lg" })}
                >
                  Contact Sales
                </a>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
