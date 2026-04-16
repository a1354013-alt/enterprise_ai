export const PrimeStubs = {
  Button: {
    props: ['label', 'icon', 'loading', 'disabled'],
    template: `<button :disabled="disabled || loading" @click="$emit('click')"><slot />{{ label }}</button>`,
  },
  Card: {
    template: `<section><header><slot name="title" /><slot name="subtitle" /></header><div><slot name="content" /></div></section>`,
  },
  InputText: {
    props: ['modelValue', 'placeholder', 'id'],
    emits: ['update:modelValue'],
    template: `<input :id="id" :placeholder="placeholder" :value="modelValue" @input="$emit('update:modelValue', $event.target.value)" />`,
  },
  Textarea: {
    props: ['modelValue', 'placeholder', 'rows'],
    emits: ['update:modelValue'],
    template: `<textarea :rows="rows" :placeholder="placeholder" :value="modelValue" @input="$emit('update:modelValue', $event.target.value)"></textarea>`,
  },
  Dropdown: {
    props: ['modelValue', 'options', 'optionLabel', 'optionValue', 'placeholder'],
    emits: ['update:modelValue'],
    template: `
      <select :value="modelValue" @change="$emit('update:modelValue', $event.target.value)">
        <option value="" disabled>{{ placeholder }}</option>
        <option v-for="opt in (options || [])" :key="String(opt[optionValue] ?? opt.value)" :value="String(opt[optionValue] ?? opt.value)">
          {{ String(opt[optionLabel] ?? opt.label) }}
        </option>
      </select>
    `,
  },
  Chips: {
    props: ['modelValue', 'separator', 'placeholder'],
    emits: ['update:modelValue'],
    template: `<input :placeholder="placeholder" :value="(modelValue || []).join(separator || ',')" @input="onInput" />`,
    methods: {
      onInput(event) {
        const sep = this.separator || ','
        const text = event.target.value || ''
        const parts = String(text)
          .split(sep)
          .map((v) => v.trim())
          .filter(Boolean)
        this.$emit('update:modelValue', parts)
      },
    },
  },
  DataTable: {
    props: ['value'],
    template: `<div><slot /></div>`,
  },
  Column: { template: `<div><slot /></div>` },
  Dialog: {
    props: ['visible', 'header', 'modal'],
    emits: ['update:visible'],
    template: `<div v-if="visible"><slot /></div>`,
  },
  Toast: { template: `<div />` },
  TabView: { template: `<div><slot /></div>` },
  TabPanel: { template: `<div><slot /></div>` },
  Password: { template: `<input type="password" />` },
}

