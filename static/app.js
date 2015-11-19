new Vue({
  el: '#app',
  data: {
    newMember: {
      name: "",
      number: "",
    },
    members: [],
  },
  methods: {
    addMember: function() {
      var name = this.newMember.name
      var number = this.newMember.number
      if (name.length && number.length) {
        this.members.push({
          name: name,
          number: number,
        })
        this.newMember.name = ""
        this.newMember.number = ""
      }
    },
    removeMember: function(index) {
      this.members.splice(index, 1)
    },
  },
})
