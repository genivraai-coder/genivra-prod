import Image from "next/image";
import { EB_Garamond } from "next/font/google";
import { cn } from "@/lib/utils";

const researchSerif = EB_Garamond({
  subsets: ["latin"],
  weight: ["500", "600"],
  display: "swap",
});

type Institution = {
  name: string;
  /** Public path under /public — omit for typography-only (Human Archive–style wordmark). */
  src?: string;
  /** Shave bottom of asset (e.g. crop marks). */
  clipBottom?: boolean;
};

/** Order and grouping inspired by Human Archive: airy row, serif names, logos only where assets exist. */
const INSTITUTIONS: Institution[] = [
  { name: "UC Berkeley" },
  { name: "Stanford", src: "/university-logos/stanford.png", clipBottom: true },
  { name: "Harvard", src: "/university-logos/harvard.png" },
];

export default function ResearchSupportedBy() {
  return (
    <section
      className="relative border-b border-white/[0.06] bg-[var(--background)] py-12 sm:py-16"
      aria-label="Research supported by"
    >
      <div className="mx-auto max-w-[1600px] px-6 sm:px-8">
        <p className="mb-10 text-center font-sans text-[11px] font-medium uppercase tracking-[0.28em] text-[#888888] sm:mb-12 md:text-[12px] md:tracking-[0.32em]">
          Research Supported By
        </p>

        <div
          className={cn(
            "mx-auto flex max-w-5xl flex-col items-center justify-center gap-10",
            "sm:flex-row sm:flex-nowrap sm:items-center sm:justify-center",
            "sm:gap-7 md:gap-9 lg:gap-11"
          )}
        >
          {INSTITUTIONS.map((inst) => (
            <div
              key={inst.name}
              className="flex items-center justify-center gap-0"
            >
              {inst.src ? (
                <Image
                  src={inst.src}
                  alt=""
                  width={132}
                  height={52}
                  className={cn(
                    "h-9 w-auto shrink-0 object-contain object-center md:h-10",
                    "-mr-1.5 sm:-mr-2 md:-mr-2.5",
                    "grayscale contrast-[1.08] brightness-[1.12]",
                    "opacity-[0.88] hover:opacity-100",
                    "transition-opacity duration-300",
                    inst.clipBottom && "[clip-path:inset(0_0_8%_0)]"
                  )}
                />
              ) : null}
              <span
                className={cn(
                  researchSerif.className,
                  "text-[1.35rem] font-medium leading-none tracking-[-0.02em] text-white/[0.82] sm:text-2xl md:text-[1.65rem] lg:text-[1.85rem]"
                )}
              >
                {inst.name}
              </span>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
