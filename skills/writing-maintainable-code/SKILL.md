---
name: writing-maintainable-code
description: Use when writing, refactoring, or reviewing code and you need to apply DRY, SOLID, and reusability/maintainability/testability/scalability (RMTS) principles - covers duplication, tight coupling, god classes, hard-to-test code, and code that won't scale.
---

# Writing Maintainable Code

## Overview

Apply DRY, SOLID, and RMTS (Reusability, Maintainability, Testability, Scalability) when writing or refactoring code. These are judgment calls, not mechanical rules — favor clarity over dogma. Premature abstraction is worse than a little duplication.

**Core principle:** Optimize for the next person who reads this code (often you, in six months). Code is read far more than it is written.

## Tradeoffs

These principles compete. When they pull opposite ways, default to the more reversible choice:

- **DRY vs simplicity** — when removing duplication would couple things that may change for different reasons, keep the duplication until the shared concept has a stable name. Copying is cheaper to undo than the wrong abstraction.
- **Scalability vs YAGNI** — make no scalability change without a named growth axis and a measured or self-evident bottleneck. "Might get big" is not a bottleneck.

## When to Use

- Writing a new feature, module, service, or class
- Refactoring code that is hard to change, test, or understand
- Reviewing a diff or PR for quality
- Symptoms: copy-pasted blocks, 300-line functions, "god" classes, `if instanceof` chains, classes you can't unit-test without a database, changes that ripple across many files

**When NOT to over-apply:** prototypes, throwaway scripts, code duplicated exactly twice with no clear shared abstraction yet (Rule of Three — wait for the third occurrence before extracting).

## DRY — Don't Repeat Yourself

Every piece of knowledge has a single, authoritative representation.

- Duplicated **logic** → extract a function/method.
- Duplicated **constants/config** → single source (const, env, config file).
- Duplicated **structure** → shared base, composition, or generics.

**Caution:** DRY is about knowledge, not text. Two code blocks that *look* identical but represent different concepts that may change independently should stay separate. Coupling unrelated things to avoid 5 duplicate lines is worse than the duplication.

## SOLID

| Letter | Principle | Smell it fixes | Apply |
|--------|-----------|----------------|-------|
| **S** | Single Responsibility | Class/function does many unrelated things; "and" in its description | One reason to change per unit. Split mixed concerns (e.g. parsing vs persistence vs formatting). |
| **O** | Open/Closed | Editing existing code every time a new variant is added | Extend via new types/strategies, not by editing switch statements. Use polymorphism/interfaces. |
| **L** | Liskov Substitution | Subclass throws or breaks when used via base type | Subtypes must honor the base contract — no narrowing inputs or surprising side effects. |
| **I** | Interface Segregation | Implementers forced to stub methods they don't use | Many small focused interfaces over one fat one. |
| **D** | Dependency Inversion | High-level code `new`s concrete deps directly | Depend on abstractions; inject dependencies. Enables swapping and mocking. |

## RMTS

- **Reusability** — write units that do one thing well with clear inputs/outputs and no hidden global state. Parameterize instead of hardcoding. A function that depends only on its args is reusable anywhere.
- **Maintainability** — clear names, small functions, shallow nesting, consistent style with the surrounding code, comments that explain *why* not *what*. Make the change easy, then make the easy change.
- **Testability** — inject dependencies (no hidden `new`, no direct singletons/clock/network inside logic), separate pure logic from I/O, keep functions deterministic. If it's hard to test, the design is too coupled — fix the design, don't skip the test.
- **Scalability** — avoid O(n²) where O(n) is easy, watch for N+1 queries, paginate/stream large sets, make services stateless so they scale horizontally, push heavy work async. Don't prematurely optimize — but don't bake in a bottleneck either.

## In Code

**DIP — inject the dependency instead of `new`ing it:**

```typescript
// Before: logic welded to a concrete client — untestable without real SMTP
class SignupService {
  register(user: User) {
    new SmtpClient("smtp.prod:25").send(user.email, "welcome");
  }
}

// After: depends on an abstraction, passed in — swap or fake it freely
interface Mailer { send(to: string, template: string): void }

class SignupService {
  constructor(private mailer: Mailer) {}
  register(user: User) {
    this.mailer.send(user.email, "welcome");
  }
}
```

**OCP — add a case without editing the dispatch:**

```typescript
// Before: every new payment type edits this function
function fee(payment: Payment): number {
  if (payment.kind === "card") return payment.amount * 0.029;
  if (payment.kind === "ach")  return 0.25;
  // ...another branch per type, forever
}

// After: new types register themselves; this code never changes again
const FEE_RULES: Record<string, (p: Payment) => number> = {};
const feeRule = (kind: string, fn: (p: Payment) => number) => { FEE_RULES[kind] = fn; };

feeRule("card", (p) => p.amount * 0.029);
feeRule("ach",  () => 0.25);

function fee(payment: Payment): number {
  return FEE_RULES[payment.kind](payment);
}
```

**Scalability — kill the N+1 with a batch:**

```typescript
// Before: one query per order — 1 + N round trips
for (const order of orders) {
  order.user = await db.fetchUser(order.userId);
}

// After: one query for all of them
const users = await db.fetchUsers(orders.map((o) => o.userId)); // single IN (...) query
for (const order of orders) {
  order.user = users[order.userId];
}
```

## Quick Workflow

1. Name the unit's single responsibility in one sentence. Can't? Split it.
2. Spot duplicated knowledge → extract (after Rule of Three).
3. Find concrete dependencies inside logic → inject them.
4. Ask "how would I unit-test this?" If the answer is "I can't without a DB/network/clock" → decouple.
5. Check the obvious scale traps: loops over data, queries in loops, unbounded result sets.

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Extracting an abstraction after seeing duplication once | Wait for Rule of Three; abstractions are expensive to undo |
| "DRY" coupling two unrelated things that just look alike | Keep separate — different reasons to change |
| God class growing because adding there is easy | Single Responsibility — split by reason-to-change |
| Hardcoded `new Service()` / direct singleton use | Inject the dependency — enables testing and swapping |
| Adding a `switch`/`if-type` branch for every new case | Open/Closed — polymorphism or strategy |
| Mixing pure logic with I/O in one function | Separate — pure core, thin I/O shell. Testable. |
| Optimizing before measuring | Avoid known traps (N+1, O(n²)); profile before micro-tuning |

## Red Flags — Stop and Reconsider

- Function longer than ~50 lines or nested 4+ deep
- "And" needed to describe what a class does
- Copy-paste with a one-word change
- Can't write a unit test without spinning up infrastructure
- Same `if (type === ...)` chain in multiple places
- A query inside a loop
