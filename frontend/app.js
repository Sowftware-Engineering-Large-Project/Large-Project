// The static preview uses session storage; the team workspace uses Flask.
const storageKey = "cle-techfest-preview-v2";
const sample = {
  festivals: [{ id: 1, name: "CLE TechFest Demo", start_date: "2026-11-20", end_date: "2026-11-21" }],
  venues: [{ id: 1, name: "Demo Hall", capacity: 30 }, { id: 2, name: "Workshop Studio", capacity: 18 }],
  events: [
    { id: 1, festival_id: 1, venue_id: 1, title: "Intro to CLE TechFest", description: "Meet the organizers and see what is on the schedule.", starts_at: "2026-11-20T10:00:00", ends_at: "2026-11-20T11:00:00", capacity: 20, status: "Scheduled" },
    { id: 2, festival_id: 1, venue_id: 2, title: "Robotics Workshop", description: "A hands-on introduction to sensors and basic controls.", starts_at: "2026-11-21T13:00:00", ends_at: "2026-11-21T14:00:00", capacity: 15, status: "Scheduled" },
  ],
  participants: [{ id: 1, name: "Demo Participant", contact_info: "demo@example.com", type: "Student" }],
  registrations: [{ id: 1, participant_id: 1, festival_id: 1, event_id: 1, status: "Active", created_at: "2026-11-20T14:30:00Z" }],
};

function readState() {
  try {
    return JSON.parse(sessionStorage.getItem(storageKey)) ?? sample;
  } catch {
    return sample;
  }
}

const live = location.pathname.startsWith("/techfest/");
let state = live ? null : readState();
const byId = (id) => document.getElementById(id);
const lookup = (table, id) => state[table].find((row) => row.id === Number(id));
const nextId = (table) => Math.max(0, ...state[table].map((row) => row.id)) + 1;
const scheduled = () => state.events.filter((event) => event.status === "Scheduled");
const timeLabel = (value) => value.slice(0, 16).replace("T", " ");

function writeState() {
  try {
    sessionStorage.setItem(storageKey, JSON.stringify(state));
    return true;
  } catch {
    return false;
  }
}

async function requestState(path, options) {
  const response = await fetch("api/" + path, options);
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.error || "The workspace could not complete the request.");
  return data;
}

function element(tag, text, className) {
  const node = document.createElement(tag);
  if (text) node.textContent = text;
  if (className) node.className = className;
  return node;
}

function showRecords(id, records, describe) {
  const container = byId(id);
  if (!container) return;
  container.replaceChildren(...(records.length
    ? records.map((row) => {
      const { title, detail, description, action } = describe(row);
      const record = element("article", "", "record");
      record.append(element("strong", title), element("p", detail));
      if (description) record.append(element("p", description));
      if (action) record.append(action);
      return record;
    })
    : [element("p", "No matching records.")]));
}

function editButton(formId, row) {
  const button = element("button", "Edit", "secondary");
  button.type = "button";
  button.addEventListener("click", () => {
    const form = byId(formId);
    form.dataset.editId = row.id;
    for (const [name, value] of Object.entries(row)) {
      const field = form.elements.namedItem(name);
      if (field) field.value = field.type === "datetime-local" ? value.slice(0, 16) : value;
    }
    form.querySelector(".feedback").textContent = "Editing record #" + row.id;
    form.querySelector(".feedback").classList.remove("error");
    form.querySelector("input").focus();
  });
  return button;
}

function fillOptions(formId, name, records, label) {
  const form = byId(formId);
  if (!form) return;
  const select = form.elements.namedItem(name);
  const oldValue = select.value;
  select.replaceChildren(new Option("Choose…", ""), ...records.map((row) => new Option(label(row), row.id)));
  if (records.some((row) => String(row.id) === oldValue)) select.value = oldValue;
}

function eventDetails(event) {
  const venue = lookup("venues", event.venue_id);
  return venue.name + " · " + timeLabel(event.starts_at) + "–" +
    timeLabel(event.ends_at) + " ET · Capacity " + event.capacity;
}

function renderEvents() {
  const search = byId("event-search");
  if (!search) return;
  const query = search.value.trim().toLowerCase();
  showRecords("event-list", scheduled().filter((event) =>
    (event.title + " " + lookup("venues", event.venue_id).name).toLowerCase().includes(query)
  ), (event) => {
    const link = element("a", "Register", "button secondary");
    link.href = "registration.html?event=" + event.id;
    return { title: event.title, detail: eventDetails(event), description: event.description, action: link };
  });
}

function render() {
  const festival = state.festivals[0];
  const festivalSummary = byId("festival-summary");
  if (festivalSummary) festivalSummary.textContent = festival
    ? festival.name + " · " + festival.start_date + " to " + festival.end_date
    : "No festival configured.";

  const stats = byId("stats");
  if (stats) stats.replaceChildren(
    element("div", scheduled().length + " scheduled events"),
    element("div", state.venues.length + " venues"),
    element("div", state.registrations.filter((row) => row.status === "Active").length + " active registrations"),
  );

  fillOptions("event-form", "venue_id", state.venues, (row) => row.name);
  fillOptions("registration-form", "participant_id", state.participants, (row) => row.name);
  fillOptions("registration-form", "event_id", scheduled(), (row) => row.title);
  showRecords("venue-list", state.venues, (row) => ({
    title: row.name, detail: "Capacity " + row.capacity, action: editButton("venue-form", row),
  }));
  showRecords("admin-event-list", state.events, (row) => ({
    title: row.title, detail: eventDetails(row) + " · " + row.status, action: editButton("event-form", row),
  }));
  showRecords("participant-list", state.participants, (row) => ({
    title: row.name, detail: row.type, action: editButton("participant-form", row),
  }));
  showRecords("registration-list", state.registrations, (row) => ({
    title: "#" + row.id + " · " + lookup("participants", row.participant_id).name,
    detail: lookup("events", row.event_id).title + " · " + row.status,
  }));
  renderEvents();
}

function positiveInteger(value) {
  return Number.isSafeInteger(value) && value > 0;
}

function saveRecord(table, existing, values) {
  if (existing) Object.assign(existing, values);
  else state[table].push({ id: nextId(table), ...values });
}

function connectForm(id, table, readValues) {
  const form = byId(id);
  if (!form) return;
  const feedback = form.querySelector(".feedback");
  const clear = () => {
    form.reset();
    delete form.dataset.editId;
    feedback.textContent = "";
    feedback.classList.remove("error");
  };
  form.querySelector("[data-reset]")?.addEventListener("click", clear);
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!state || form.dataset.saving) return;
    const data = new FormData(form);
    const field = (name) => String(data.get(name) ?? "").trim();
    const existing = lookup(table, form.dataset.editId);
    const result = readValues(field, existing);
    if (result.error) {
      feedback.textContent = result.error;
      feedback.classList.add("error");
      return;
    }
    const submit = form.querySelector("button:not([type]), button[type=submit]");
    form.dataset.saving = "true";
    submit.disabled = true;
    try {
      let message = result.message;
      if (live) {
        state = await requestState(table + (existing ? "/" + existing.id : ""), {
          method: existing ? "PATCH" : "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(result.values),
        });
        message = "Saved to the team database.";
      } else {
        saveRecord(table, existing, result.values);
        if (!writeState()) message += " Browser storage is unavailable.";
      }
      clear();
      render();
      feedback.textContent = message;
    } catch (error) {
      feedback.textContent = error.message;
      feedback.classList.add("error");
    } finally {
      delete form.dataset.saving;
      submit.disabled = false;
    }
  });
}

connectForm("venue-form", "venues", (field, existing) => {
  const name = field("name");
  const capacity = Number(field("capacity"));
  if (!name || !positiveInteger(capacity)) return { error: "Enter a venue name and positive whole-number capacity." };
  if (existing && scheduled().some((event) => event.venue_id === existing.id && event.capacity > capacity)) {
    return { error: "This capacity is below that of a scheduled event at the venue." };
  }
  return { values: { name, capacity }, message: "Venue saved in the preview." };
});

connectForm("event-form", "events", (field, existing) => {
  const title = field("title");
  const description = field("description");
  const starts = field("starts_at");
  const ends = field("ends_at");
  const capacity = Number(field("capacity"));
  const venue = lookup("venues", field("venue_id"));
  const festival = existing ? lookup("festivals", existing.festival_id) : state.festivals[0];
  if (!festival) return { error: "Initialize a festival before adding events." };
  if (!title || !description || !venue) return { error: "Enter a title and description, and choose a venue." };
  if (!starts || !ends || ends <= starts) return { error: "The event must end after it starts." };
  if (starts.slice(0, 10) < festival.start_date || ends.slice(0, 10) > festival.end_date) {
    return { error: "Keep the event within " + festival.start_date + " to " + festival.end_date + "." };
  }
  if (!positiveInteger(capacity) || capacity > venue.capacity) {
    return { error: "Enter a positive whole-number capacity no greater than the venue capacity." };
  }
  return {
    values: { festival_id: festival.id, venue_id: venue.id, title, description, starts_at: starts.slice(0, 16) + ":00", ends_at: ends.slice(0, 16) + ":00", capacity, status: existing?.status ?? "Scheduled" },
    message: "Event saved in the preview.",
  };
});

connectForm("participant-form", "participants", (field) => {
  const name = field("name");
  const contact_info = field("contact_info");
  const type = field("type");
  if (!name || !contact_info) return { error: "Enter a name and contact information." };
  return { values: { name, contact_info, type }, message: "Participant saved in the preview." };
});

connectForm("registration-form", "registrations", (field) => {
  const participant = lookup("participants", field("participant_id"));
  const event = lookup("events", field("event_id"));
  if (!participant || event?.status !== "Scheduled") return { error: "Choose a participant and a scheduled event." };
  return {
    values: { participant_id: participant.id, festival_id: event.festival_id, event_id: event.id, status: "Active", created_at: new Date().toISOString() },
    message: "Registration saved in the preview.",
  };
});

byId("event-search")?.addEventListener("input", () => {
  if (state) renderEvents();
});

function showPage() {
  render();
  const registrationForm = byId("registration-form");
  const eventId = new URLSearchParams(location.search).get("event");
  if (registrationForm && lookup("events", eventId)?.status === "Scheduled") {
    registrationForm.elements.namedItem("event_id").value = eventId;
  }
}

async function loadWorkspace() {
  const notice = element("p", "Loading team data…", "workspace-status");
  document.querySelector("main").prepend(notice);
  notice.setAttribute("role", "status");
  const buttons = document.querySelectorAll("form button:not([type]), form button[type=submit]");
  buttons.forEach((button) => { button.disabled = true; });
  try {
    state = await requestState("state");
    showPage();
    buttons.forEach((button) => { button.disabled = false; });
    notice.remove();
  } catch (error) {
    notice.textContent = "Unable to load team data. " + error.message;
  }
}

if (live) {
  const footer = document.querySelector(".site-footer span");
  if (footer) footer.textContent = "Team workspace · Use fictional information only.";
  loadWorkspace();
} else {
  showPage();
}
