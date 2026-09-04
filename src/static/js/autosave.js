(() => {
  "use strict";

  const form = document.querySelector("#note-form");
  if (!form) return;

  const status = document.querySelector("#save-status");
  const timestamp = document.querySelector("#updated-at");
  const displayTime = document.querySelector("#updated-display");
  const trackedFields = [...form.querySelectorAll("input[name='title'], textarea[name='body']")];
  let lastSaved = trackedFields.map((field) => field.value).join("\u0000");
  let saving = false;
  let queued = false;

  const values = () => trackedFields.map((field) => field.value).join("\u0000");
  const setStatus = (message, state = "") => {
    status.textContent = message;
    status.dataset.state = state;
  };

  async function save() {
    if (values() === lastSaved) return;
    if (saving) {
      queued = true;
      return;
    }

    saving = true;
    setStatus("Saving…", "saving");
    const submittedValues = values();

    try {
      const response = await fetch(form.dataset.autosaveUrl, {
        method: "POST",
        body: new FormData(form),
        headers: { "X-Requested-With": "XMLHttpRequest" },
      });
      const result = await response.json();
      if (response.status === 409) {
        setStatus("Changed elsewhere — reload before saving", "error");
        return;
      }
      if (!response.ok) {
        setStatus("Could not save — check the fields", "error");
        return;
      }

      lastSaved = submittedValues;
      timestamp.value = result.updated_at;
      displayTime.textContent = result.display_time;
      displayTime.dateTime = result.updated_at;
      setStatus("Saved", "saved");
    } catch (_error) {
      setStatus("Offline — use Save when reconnected", "error");
    } finally {
      saving = false;
      if (queued) {
        queued = false;
        void save();
      }
    }
  }

  trackedFields.forEach((field) => {
    field.addEventListener("input", () => setStatus("Unsaved", "dirty"));
    field.addEventListener("blur", () => void save());
  });
})();
